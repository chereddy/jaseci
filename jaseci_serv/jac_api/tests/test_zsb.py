from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from jaseci.actions.module.ai_serving_api import check_model_live
from jaseci.utils.utils import TestCaseHelper
from jaseci.element import element
from django.test import TestCase
import uuid
import base64


class test_zsb(TestCaseHelper, TestCase):
    """Test the authorized user node API"""

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(
            'JSCITfdfdEST_test@jaseci.com',
            'password'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.master = self.user.get_master()
        payload = {'op': 'create_graph', 'name': 'Something'}
        res = self.client.post(reverse(f'jac_api:{payload["op"]}'), payload)
        self.gph = self.master._h.get_obj(uuid.UUID(res.data['jid']))
        payload = {'op': 'create_sentinel', 'name': 'Something'}
        res = self.client.post(reverse(f'jac_api:{payload["op"]}'), payload)
        self.snt = self.master._h.get_obj(uuid.UUID(res.data['jid']))
        ll_file = base64.b64encode(
            open("jac_api/tests/zsb.jac").read().encode())
        payload = {'op': 'set_jac', 'snt': self.snt.id.urn,
                   'code': ll_file, 'encoded': True}
        res = self.client.post(
            reverse(f'jac_api:{payload["op"]}'), payload, format='json')
        self.run_walker('init', {})

    def tearDown(self):
        super().tearDown()

    def run_walker(self, w_name, ctx, prime=None):
        """Helper to make calls to execute walkers"""
        if(not prime):
            payload = {'snt': self.snt.id.urn, 'name': w_name,
                       'nd': self.gph.id.urn, 'ctx': ctx}
        else:
            payload = {'snt': self.snt.id.urn, 'name': w_name,
                       'nd': prime, 'ctx': ctx}
        res = self.client.post(
            reverse(f'jac_api:prime_run'), payload, format='json')
        return res.data

    def test_zsb_create_answer(self):
        """Test ZSB Create Answer call USE api"""
        if (not check_model_live('USE')):
            self.skipTest("external resource not available")
        data = self.run_walker('add_bot', {'name': "Bot"})
        self.assertEqual(data[0]['kind'], 'bot')
        bot_jid = data[0]['jid']
        data = self.run_walker('create_answer', {'text': "Yep"}, prime=bot_jid)
        self.assertEqual(data[0]['kind'], 'answer')

    def test_zsb_ask_question(self):
        """Test ZSB Create Answer call USE api"""
        if (not check_model_live('USE')):
            self.skipTest("external resource not available")
        data = self.run_walker('add_bot', {'name': "Bot"})
        self.assertEqual(data[0]['kind'], 'bot')
        bot_jid = data[0]['jid']
        data = self.run_walker('create_answer', {'text': "Yep"}, prime=bot_jid)
        data = self.run_walker(
            'create_answer', {'text': "Nope"}, prime=bot_jid)
        data = self.run_walker(
            'create_answer', {'text': "Maybe"}, prime=bot_jid)
        data = self.run_walker(
            'ask_question', {'text': "Who says yep?"}, prime=bot_jid)
        data = self.run_walker(
            'get_log', {}, prime=bot_jid)
        self.assertEqual(data[0][0][1], 'Who says yep?')

    def test_zsb_ask_question_multi(self):
        """Test ZSB Create Answer call USE api"""
        if (not check_model_live('USE')):
            self.skipTest("external resource not available")
        data = self.run_walker('add_bot', {'name': "Bot"})
        self.assertEqual(data[0]['kind'], 'bot')
        bot_jid = data[0]['jid']
        data = self.run_walker('create_answer', {'text': "Yep"}, prime=bot_jid)
        data = self.run_walker(
            'create_answer', {'text': "Nope"}, prime=bot_jid)
        data = self.run_walker(
            'create_answer', {'text': "Maybe"}, prime=bot_jid)
        data = self.run_walker(
            'ask_question', {'text': "Who says yep?"}, prime=bot_jid)
        data = self.run_walker(
            'ask_question', {'text': "Who says yep?"}, prime=bot_jid)
        data = self.run_walker(
            'ask_question', {'text': "Who says yep?"}, prime=bot_jid)
        data = self.run_walker(
            'get_log', {}, prime=bot_jid)
        self.assertEqual(data[0][0][1], 'Who says yep?')

    def test_dangling_edge_corruption_healing_non_block(self):
        """Test ZSB Create Answer call USE api"""
        if (not check_model_live('USE')):
            self.skipTest("external resource not available")
        data = self.run_walker('add_bot', {'name': "Bot"})
        self.assertEqual(data[0]['kind'], 'bot')
        bot_jid = data[0]['jid']
        data = self.run_walker('create_answer', {'text': "Yep"}, prime=bot_jid)
        data = self.run_walker(
            'create_answer', {'text': "Nope"}, prime=bot_jid)
        lostnode_jid = data[0]['jid']
        element.destroy(self.master._h.get_obj(uuid.UUID(lostnode_jid)))
        data = self.run_walker(
            'create_answer', {'text': "Maybe"}, prime=bot_jid)
        data = self.run_walker(
            'ask_question', {'text': "Who says yep?"}, prime=bot_jid)
        data = self.run_walker(
            'get_log', {}, prime=bot_jid)
        self.assertEqual(data[0][0][1], 'Who says yep?')
        data = self.run_walker(
            'delete_bot', {}, prime=bot_jid)