#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "data.h"

static PyObject *f_account_resource_from_lcs(PyObject *self, PyObject *args) {
    PyBytesObject* bytes;

    /* Parse arguments */
    if(!PyArg_ParseTuple(args, "S", &bytes)) {
        return NULL;
    }

    struct CDevAccountResource result = account_resource_from_lcs((const uint8_t*) PyBytes_AsString(bytes), PyBytes_Size(bytes));

    PyObject* obj = PyDict_New();
    PyDict_SetItem(obj, PyUnicode_FromString("balance"), PyLong_FromUnsignedLongLong(result.balance));

    return obj;
}

static PyMethodDef pyLibraMethods[] = {
        {"account_resource_from_lcs", f_account_resource_from_lcs, METH_VARARGS, "parse account_state_blob"},
        {NULL, NULL, 0, NULL}
};


static struct PyModuleDef pyLibraModule = {
        PyModuleDef_HEAD_INIT,
        "_pylibra",
        "Python interface for the libra-dev library",
        -1,
        pyLibraMethods
};

PyMODINIT_FUNC PyInit__pylibra(void) {
    return PyModule_Create(&pyLibraModule);
}

/*
PyMODINIT_FUNC
PyInit_pyLibra(void)
{
    PyObject *m;
    if (PyType_Ready(&pyLibraAccountResourceType) < 0)
        return NULL;

    m = PyModule_Create(&pyLibraModule);
    if (m == NULL)
        return NULL;

    Py_INCREF(&pyLibraAccountResourceType);
    if (PyModule_AddObject(m, "Custom", (PyObject *) &pyLibraAccountResourceType) < 0) {
        Py_DECREF(&pyLibraAccountResourceType);
        PY_DECREF(m);
        return NULL;
    }

    return m;
}
*/