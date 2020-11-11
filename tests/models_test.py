from mongoengine import connect

from app.models import *

con = connect('SpinachTest')


def test_match_and_transaction():
    match = Match.add_match(name='Test1', description='For Test', member=['Explosive', 'arily'],
                            adder_qq=496802290)
    Transaction.add_transaction(496802290, -150, 'Bets', target='arily', match=match)
    Transaction.add_transaction(496802291, -20, 'Bets', target='Explosive', match=match)
    Transaction.add_transaction(496802292, -40, 'Bets', target='arily', match=match)
    Transaction.add_transaction(496802293, -60, 'Bets', target='Explosive', match=match)

    match.calc_bets('Explosive')


def clear():
    Match.drop_collection()
    Transaction.drop_collection()
    User.drop_collection()


clear()
test_match_and_transaction()
