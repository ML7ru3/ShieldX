import numpy as np
from unittest.mock import MagicMock, patch

import pytest

DROP_FIELDS = ['SourceIP', 'SourcePort', 'DestinationIP', 'DestinationPort', 'Duration']


@pytest.fixture(autouse=True)
def reset_models():
    from domains import pipeline
    pipeline._model = None
    pipeline._l1_model = None
    yield


class TestLoadModel:
    @patch('domains.pipeline.xgb.XGBClassifier')
    def test_load_model_success(self, MockXGB):
        from domains.pipeline import load_model

        instance = MockXGB.return_value
        mdl = load_model()
        instance.load_model.assert_called_once_with('xgboost_model.json')
        assert mdl is instance

    @patch('domains.pipeline.xgb.XGBClassifier')
    def test_load_model_cached(self, MockXGB):
        from domains.pipeline import load_model

        first = load_model()
        second = load_model()
        assert first is second
        assert MockXGB.return_value.load_model.call_count == 1


class TestPredict:
    @patch('domains.pipeline.load_model')
    def test_predict_dict_benign(self, mock_load):
        from domains.pipeline import predict

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0])
        mock_load.return_value = mock_model

        result = predict({'feature': 1.0})
        assert result == 0

    @patch('domains.pipeline.load_model')
    def test_predict_dict_malware(self, mock_load):
        from domains.pipeline import predict

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([1])
        mock_load.return_value = mock_model

        result = predict({'feature': 99.0})
        assert result == 1

    @patch('domains.pipeline.load_model')
    def test_predict_empty_dict(self, mock_load):
        from domains.pipeline import predict

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0])
        mock_load.return_value = mock_model

        result = predict({})
        assert result == 0

    def test_filter_model_features_drops_fields(self):
        from domains.pipeline import filter_model_features
        base = {key: f"val_{key}" for key in DROP_FIELDS}
        base["some_good_field"] = 42
        out = filter_model_features(base)
        assert set(out.keys()) == {"some_good_field"}

    def test_filter_model_features_noop(self):
        from domains.pipeline import filter_model_features
        simple = {"only": 1, "nonforbidden": 2}
        out = filter_model_features(simple)
        assert out == simple


class TestLoadL1Model:
    @patch('domains.pipeline.xgb.XGBClassifier')
    def test_load_l1_model_success(self, MockXGB):
        from domains.pipeline import load_l1_model

        instance = MockXGB.return_value
        mdl = load_l1_model()
        instance.load_model.assert_called_once_with('l1_xgboost_model.json')
        assert mdl is instance

    @patch('domains.pipeline.xgb.XGBClassifier')
    def test_load_l1_model_cached(self, MockXGB):
        from domains.pipeline import load_l1_model

        first = load_l1_model()
        second = load_l1_model()
        assert first is second
        assert MockXGB.return_value.load_model.call_count == 1


class TestPredictL1:
    @patch('domains.pipeline.load_l1_model')
    def test_predict_l1_nondoh(self, mock_load):
        from domains.pipeline import predict_l1

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0])
        mock_load.return_value = mock_model

        result = predict_l1({'feature': 1.0})
        assert result == 0

    @patch('domains.pipeline.load_l1_model')
    def test_predict_l1_doh(self, mock_load):
        from domains.pipeline import predict_l1

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([1])
        mock_load.return_value = mock_model

        result = predict_l1({'feature': 99.0})
        assert result == 1


class TestCaptureAndPredict:
    @patch('domains.pipeline.AsyncSniffer')
    @patch('domains.pipeline.load_l1_model')
    @patch('domains.pipeline.load_model')
    @patch('domains.pipeline.time.sleep')
    def test_empty_capture(self, mock_sleep, mock_load, mock_load_l1, mock_sniffer):
        from domains.pipeline import capture_and_predict

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0])
        mock_load.return_value = mock_model
        mock_load_l1.return_value = mock_model

        results = capture_and_predict(interface='eth0', sniff_duration=1)
        assert isinstance(results, list)

    @patch('domains.pipeline.AsyncSniffer')
    @patch('domains.pipeline.load_l1_model')
    @patch('domains.pipeline.load_model')
    @patch('domains.pipeline.time.sleep')
    def test_model_error_handling(self, mock_sleep, mock_load, mock_load_l1, mock_sniffer):
        from domains.pipeline import capture_and_predict

        mock_model = MagicMock()
        mock_model.predict.side_effect = ValueError("model failure")
        mock_load.return_value = mock_model
        mock_load_l1.return_value = mock_model

        results = capture_and_predict(interface='eth0', sniff_duration=1)
        assert isinstance(results, list)
        assert len(results) == 0


class TestFlowCollector:
    def test_no_file_created(self):
        from domains.pipeline import FlowCollector

        collector = FlowCollector()
        assert collector.output_file == '/dev/null'

    def test_garbage_collect_empty(self):
        from domains.pipeline import FlowCollector

        collector = FlowCollector()
        collector.garbage_collect(None)
        assert len(collector.flows) == 0

    def test_garbage_collect_removes_expired(self):
        from domains.pipeline import FlowCollector
        from unittest.mock import MagicMock

        collector = FlowCollector()
        mock_flow = MagicMock()
        mock_flow.latest_timestamp = 0
        mock_flow.duration = 999
        collector.flows[("key", 0)] = mock_flow

        collector.garbage_collect(latest_time=1000)
        assert len(collector.flows) == 0
