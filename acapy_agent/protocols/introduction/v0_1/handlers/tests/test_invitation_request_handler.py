from unittest import IsolatedAsyncioTestCase

from ......messaging.base_handler import HandlerException
from ......messaging.request_context import RequestContext
from ......messaging.responder import MockResponder
from ......protocols.connections.v1_0.messages.connection_invitation import (
    ConnectionInvitation,
)
from ......tests import mock
from ......utils.testing import create_test_profile
from ...messages.invitation import Invitation
from ...messages.invitation_request import InvitationRequest
from .. import invitation_request_handler as test_module

TEST_DID = "55GkHamhTU1ZbTbV2ab9DE"
TEST_VERKEY = "3Dn1SJNPaCXcvvJvSbsFWP2xaCjMom3can8CQNhWrTRx"
TEST_ROUTE_VERKEY = "9WCgWKUaAJj3VWxxtzvvMQN3AoFxoBtBDo9ntwJnVVCC"
TEST_LABEL = "Label"
TEST_ENDPOINT = "http://localhost"
TEST_IMAGE_URL = "http://aries.ca/images/sample.png"


class TestInvitationRequestHandler(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.context = RequestContext.test_context(await create_test_profile())
        self.context.connection_ready = True
        self.context.message = InvitationRequest(
            responder="test-agent",
            message="Hello World",
        )
        self.context.update_settings({"auto_accept_intro_invitation_requests": False})

    async def test_handle(self):
        handler = test_module.InvitationRequestHandler()

        responder = MockResponder()

        with mock.patch.object(test_module, "ConnectionManager", autospec=True):
            await handler.handle(self.context, responder)

    async def test_handle_auto_accept(self):
        handler = test_module.InvitationRequestHandler()
        self.context.update_settings({"auto_accept_intro_invitation_requests": True})

        conn_invitation = ConnectionInvitation(
            label=TEST_LABEL,
            did=TEST_DID,
            recipient_keys=[TEST_VERKEY],
            endpoint=TEST_ENDPOINT,
            routing_keys=[TEST_ROUTE_VERKEY],
            image_url=TEST_IMAGE_URL,
        )
        mock_conn_rec = mock.MagicMock(connection_id="dummy")

        responder = MockResponder()
        with mock.patch.object(
            test_module, "ConnectionManager", autospec=True
        ) as mock_mgr:
            mock_mgr.return_value.create_invitation = mock.CoroutineMock(
                return_value=(mock_conn_rec, conn_invitation)
            )

            await handler.handle(self.context, responder)
            mock_mgr.return_value.create_invitation.assert_called_once_with()

            messages = responder.messages
            assert len(messages) == 1
            (result, _) = messages[0]
            assert type(result) is Invitation
            assert result._thread._thid == self.context.message._message_id

    async def test_handle_not_ready(self):
        handler = test_module.InvitationRequestHandler()
        self.context.connection_ready = False

        with self.assertRaises(HandlerException):
            await handler.handle(self.context, None)
