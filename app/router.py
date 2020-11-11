import datetime
from typing import List

from fastapi import FastAPI, Depends, Request, Response, HTTPException, Path
from fastapi import status as status_hint
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from mongoengine import connect

import app.models as models
import app.schemas as schemas

app = FastAPI(title='OCL菠菜系统', version='0.01', description='想玩菠菜就给我好好去打课题曲！')

origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def make_response(message: str, status: str = 'success', *args, **kwargs):
    return {'message': message, 'status': status, 'response_time': datetime.datetime.utcnow(), **kwargs}


@app.on_event("startup")
async def startup_event():
    connect('ocl_spinach')


@app.get('/match',
         summary='获取所有Pending状态的对局。')
async def get_matches():
    return models.Match.get_pending_matches()


@app.post('/match',
          summary='添加一场对局。')
async def add_match(*,
                    payload: schemas.MatchSchemas
                    ):
    if matches := models.Match.get_pending_matches():
        if payload.name in [match.get('name') for match in matches]:
            return make_response('名称重复，请更改后再尝试添加对局。', status='failed')
    models.Match.add_match(**dict(payload))
    return make_response('添加对局成功。')


@app.get('/match/<match_id>',
         summary='查看单场对局详细信息。')
async def get_match(*, match_id: str):
    match = models.Match.get_match(match_id)
    return {
        'name': match.name,
        'description': match.description,
        'member': match.member,
        'start_time': match.start_time,
        'adder_qq': match.adder_qq,
        'status': match.status,
        'total_bets': match.total_bets,
        'match_id': match.match_id,
        'winner': match.winner
    }


@app.post('/match/<match_id>/bet',
          summary='下注对局。')
async def place_bet(*,
                    match_id: str,
                    payload: schemas.PlaceBetSchemas
                    ):
    if match := models.Match.get_match(match_id):
        if payload.target in match.member:
            if ts := models.Transaction.add_transaction(
                    qq=payload.qq,
                    amount=-payload.amount,
                    action='Bet',
                    target=payload.target,
                    match=match):
                match.calc_bets()
                return make_response('下注成功!', current_balance=ts)
            return make_response('下注失败，您的余额不足', status='failed',
                                 current_balance=models.User.get_user(payload.qq).balance)
        return make_response('下注失败，目标不在对局中', status='failed')


@app.post('/match/<match_id>/finished',
          summary='结束并结算对局。')
async def finish_match(*,
                       match_id: str,
                       winner: str
                       ):
    if match := models.Match.get_match(match_id):
        if match.status != 'Finished':
            match.finish_match(winner)
            return make_response('结算成功。', match_id=match_id)
        return make_response('本场对局已经结算', status='failed')
