from __future__ import annotations

import datetime
from typing import List, Optional
from collections import defaultdict
from mongoengine import (
    DateTimeField,
    StringField,
    LazyReferenceField,
    GenericLazyReferenceField,
    DynamicDocument,
    DictField,
    CASCADE,
    IntField,
    LongField,
    ListField,
    PULL,
    FloatField
)


class Match(DynamicDocument):
    name = StringField(required=True, unique=True)
    description = StringField(required=True)
    member = DictField(required=True)
    start_time = DateTimeField(default=datetime.datetime.utcnow)
    status = StringField(choices=['Pending', 'Finished'], default='Pending')
    adder_qq = LongField(required=True)

    total_bets = IntField(default=0)
    match_id = IntField(default=0)
    winner = StringField(default='')

    # transaction_id = ListField(LazyReferenceField('Transaction', ))

    @classmethod
    def add_match(
            cls,
            name: str,
            description: str,
            member: List[str],
            adder_qq: int
    ) -> Match:
        return cls(
            name=name,
            description=description,
            member={u: 0 for u in member},
            adder_qq=adder_qq
        ).save()

    @classmethod
    def get_match(cls, match_object_id: Match.id) -> Optional[Match]:
        if match := cls.objects(id=match_object_id).first():
            return match

    @classmethod
    def get_pending_matches(cls) -> List[Optional[dict]]:
        return [{'id': str(i.id),
                 'name': i.name,
                 'description': i.description,
                 'member': [name for name in i.member.keys()],
                 'start_time': i.start_time}
                for i in cls.objects(status='Pending').all()]

    def calc_bets(self, winner: str = None) -> dict:
        if self.status == 'Pending':
            member = {u: 0 for u in self.member}
            ts = Transaction.objects(action_id=self).all()

            winner_transactions = []
            for t in ts:
                member[t.target] += t.amount
                if t.target == winner:
                    winner_transactions.append(t)
            total_bets = sum([v for v in member.values()])
            self.modify(member=member, total_bets=total_bets, winner=winner)

            if winner:
                for user in winner_transactions:
                    benefits_percentage = user.amount / member[winner]
                    Transaction.add_transaction(user.qq,
                                                abs(user.amount + (total_bets - member[winner]) * benefits_percentage),
                                                'Reward',
                                                match=self)
            return {'winner_users': [user.qq for user in winner_transactions], 'total_bets': total_bets}

    def finish_match(self, winner: str):
        self.calc_bets(winner)
        self.modify(status='Finished')


class User(DynamicDocument):
    qq = LongField(required=True, unique=True)
    osu_id = IntField()
    balance = IntField(required=True, default=100)

    @classmethod
    def get_user(cls, qq: int) -> Optional[User]:
        return cls.objects(qq=qq).first()

    @classmethod
    def add_user(cls, qq: int) -> User:
        return cls(qq=qq).save()

    def update_balance(self) -> int:
        total = Transaction.objects(qq=self.qq).sum('amount')
        left_balance = 100 + total
        self.modify(balance=left_balance)
        return left_balance


class Mission(DynamicDocument):
    beatmapset_id = IntField(required=True)
    grade = StringField()
    combo = IntField()
    accuracy = FloatField()
    passed = IntField()
    mods = IntField()

    max_completer = IntField()

    description = StringField()
    release_time = DateTimeField(default=datetime.datetime.utcnow)

    completer = DictField(default={})


class Transaction(DynamicDocument):
    qq = LongField(required=True)
    amount = IntField(required=True)

    target = StringField()
    action = StringField(choices=['Mission', 'Reward', 'Bet', 'Bonus'])
    action_id = GenericLazyReferenceField(choices=[Match, Mission], required=True)

    @classmethod
    def add_transaction(
            cls,
            qq: int,
            amount: int,
            action: str,
            target: str = None,
            match: Match = None,
            mission: Mission = None
    ) -> Optional[int]:
        if not (user := User.get_user(qq)):
            user = User.add_user(qq)

        if match:
            if user.balance + amount < 0:
                return
        action_id = match or mission
        cls(qq=qq, amount=amount, action=action, target=target, action_id=action_id).save()
        return user.update_balance()


Match.register_delete_rule(Transaction, 'action_id', CASCADE)
