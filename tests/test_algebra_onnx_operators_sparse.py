# SPDX-License-Identifier: Apache-2.0

import unittest
import packaging.version as pv
import warnings
import numpy as np
from numpy.testing import assert_almost_equal
from scipy.sparse import coo_matrix
from onnxruntime import InferenceSession, __version__ as ort_version
try:
    from onnxruntime.capi.onnxruntime_pybind11_state import (
        InvalidArgument as OrtInvalidArgument
    )
except ImportError:
    OrtInvalidArgument = None
from skl2onnx.common.data_types import FloatTensorType
from skl2onnx.algebra.onnx_ops import OnnxAdd
try:
    from skl2onnx.algebra.onnx_ops import OnnxConstantOfShape
except ImportError:
    # onnx is too old.
    OnnxConstantOfShape = None
from test_utils import TARGET_OPSET

THRESHOLD = "1.3.0"


class TestOnnxOperatorsSparse(unittest.TestCase):

    @unittest.skipIf(TARGET_OPSET < 11,
                     reason="only available for opset >= 11")
    @unittest.skipIf(pv.Version(ort_version) < pv.Version(THRESHOLD),
                     reason="fails with onnxruntime < %s" % THRESHOLD)
    def test_onnx_init_dense(self):
        X = np.array([1, 2, 3, 4, 5, 6]).astype(np.float32).reshape((3, 2))

        node = OnnxAdd('X', X, output_names=['Y'], op_version=TARGET_OPSET)

        model_def = node.to_onnx({'X': X},
                                 outputs=[('Y', FloatTensorType())])

        sess = InferenceSession(model_def.SerializeToString())
        res = sess.run(None, {'X': X})[0]

        assert_almost_equal(X + X, res)

    @unittest.skipIf(TARGET_OPSET < 11,
                     reason="only available for opset >= 11")
    @unittest.skipIf(pv.Version(ort_version) < pv.Version(THRESHOLD),
                     reason="fails with onnxruntime < %s" % THRESHOLD)
    def test_onnx_init_sparse_coo(self):
        row = np.array([0, 0, 1, 3, 1], dtype=np.float32)
        col = np.array([0, 2, 1, 3, 1], dtype=np.float32)
        data = np.array([1, 1, 1, 1, 1], dtype=np.float32)
        X = coo_matrix((data, (row, col)), shape=(4, 4))

        node = OnnxAdd(
            'X', X, output_names=['Y'],
            op_version=TARGET_OPSET)

        model_def = node.to_onnx(
            {'X': X}, outputs=[('Y', FloatTensorType())])

        try:
            sess = InferenceSession(model_def.SerializeToString())
        except (RuntimeError, OrtInvalidArgument):
            # Sparse tensor is not supported for constant.
            return
        try:
            res = sess.run(None, {'X': X})[0]
        except RuntimeError as e:
            # Sparse tensor is not supported for constant.
            warnings.warn(
                "Unable to run with %r\n---\n%s\n%s" % (
                    {'X': X}, model_def, e))
            return
        assert_almost_equal(X + X, res)


if __name__ == "__main__":
    unittest.main()
