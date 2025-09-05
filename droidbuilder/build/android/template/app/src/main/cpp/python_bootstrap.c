#include <jni.h>
#include <string.h>
#include <android/log.h>
#include <Python.h> // This will be available after Python is built and installed

#define LOG_TAG "PythonBootstrap"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Function to initialize Python and run a script
JNIEXPORT void JNICALL
Java_com_example_myapp_MainActivity_startPython(
    JNIEnv *env,
    jobject thiz,
    jstring pythonHome,
    jstring pythonPath,
    jstring mainFile) {

    const char *pyHome = (*env)->GetStringUTFChars(env, pythonHome, 0);
    const char *pyPath = (*env)->GetStringUTFChars(env, pythonPath, 0);
    const char *mainPyFile = (*env)->GetStringUTFChars(env, mainFile, 0);

    LOGI("Setting PYTHONHOME: %s", pyHome);
    Py_SetPythonHome(Py_DecodeLocale(pyHome, NULL));

    LOGI("Setting PYTHONPATH: %s", pyPath);
    Py_SetPath(Py_DecodeLocale(pyPath, NULL));

    LOGI("Initializing Python interpreter...");
    Py_InitializeEx(0); // Initialize with no signal handlers

    if (!Py_IsInitialized()) {
        LOGE("Failed to initialize Python interpreter.");
        return;
    }

    LOGI("Running Python script: %s", mainPyFile);
    PyObject *pName, *pModule, *pFunc, *pArgs, *pValue;

    // Add current directory to sys.path
    PyObject *sys_path = PySys_GetObject("path");
    if (sys_path) {
        PyList_Append(sys_path, PyUnicode_DecodeFSDefault("."));
    }

    pName = PyUnicode_DecodeFSDefault(mainPyFile);
    if (!pName) {
        LOGE("Failed to decode main file name.");
        goto error;
    }

    pModule = PyImport_Import(pName);
    Py_DECREF(pName);

    if (!pModule) {
        LOGE("Failed to import main module.");
        if (PyErr_Occurred()) {
            PyErr_Print();
        }
        goto error;
    }

    // You can add logic here to call a specific function in your Python script
    // For now, we just import it, which will run the top-level code.

    LOGI("Python script execution finished.");

error:
    if (PyErr_Occurred()) {
        PyErr_Print();
    }
    Py_Finalize(); // Finalize the interpreter
    LOGI("Python interpreter finalized.");

    (*env)->ReleaseStringUTFChars(env, pythonHome, pyHome);
    (*env)->ReleaseStringUTFChars(env, pythonPath, pyPath);
    (*env)->ReleaseStringUTFChars(env, mainFile, mainPyFile);
}