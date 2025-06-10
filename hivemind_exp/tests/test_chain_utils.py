import unittest
import pytest
import json

from hivemind_exp.chain_utils import ModalSwarmCoordinator
from web3 import Web3
from unittest.mock import patch, MagicMock, Mock
from requests import HTTPError, Response


def test_register_peer_raises_on_server_error():
    with patch("hivemind_exp.chain_utils.send_via_api") as mock_send_via_api:
        err_response = Response()
        err_response.status_code = 500
        mock_send_via_api.side_effect = HTTPError(response=err_response)
        coordinator = ModalSwarmCoordinator(Web3(), "", "")

        with pytest.raises(HTTPError) as exc_info:
            coordinator.register_peer("QmTestPeer")

        assert exc_info.type is HTTPError
        assert 500 == exc_info.value.response.status_code
        mock_send_via_api.assert_called_once()


def test_register_peer_raises_on_unknown_bad_request_error():
    with patch("hivemind_exp.chain_utils.send_via_api") as mock_send_via_api:
        err_response = MagicMock()
        err_response.status_code = 400
        err_response.json.return_value = {"error": "unknown bad request"}
        mock_send_via_api.side_effect = HTTPError(response=err_response)
        coordinator = ModalSwarmCoordinator(Web3(), "", "")

        with pytest.raises(HTTPError) as exc_info:
            coordinator.register_peer("QmTestPeer")

        assert exc_info.type is HTTPError
        assert 400 == exc_info.value.response.status_code

        mock_send_via_api.assert_called_once()


def test_register_peer_raises_on_when_fails_to_decode():
    with patch("hivemind_exp.chain_utils.send_via_api") as mock_send_via_api:
        err_response = MagicMock()
        err_response.status_code = 400
        err_response.json.side_effect = json.JSONDecodeError("", "", 0)
        mock_send_via_api.side_effect = HTTPError(response=err_response)
        coordinator = ModalSwarmCoordinator(Web3(), "", "")

        with pytest.raises(HTTPError) as exc_info:
            coordinator.register_peer("QmTestPeer")

        assert exc_info.type is HTTPError
        assert 400 == exc_info.value.response.status_code

        mock_send_via_api.assert_called_once()


def test_register_peer_continues_on_already_registered():
    with patch("hivemind_exp.chain_utils.send_via_api") as mock_send_via_api:
        err_response = MagicMock()
        err_response.status_code = 400
        err_response.json.return_value = {"error": "PeerIdAlreadyRegistered"}
        mock_send_via_api.side_effect = HTTPError(response=err_response)
        coordinator = ModalSwarmCoordinator(Web3(), "", "")

        try:
            coordinator.register_peer("QmTestPeer")
        except Exception:
            pytest.fail("register_peer should not fail when peer already registered")

        mock_send_via_api.assert_called_once()
