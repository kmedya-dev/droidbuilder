package com.example.myapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import com.example.myapp.ui.theme.MyDroidAppTheme
import android.content.Context
import android.util.Log
import java.io.File
import android.os.Build

class MainActivity : ComponentActivity() {

    companion object {
        init {
            System.loadLibrary("python_bootstrap")
        }
    }

    private external fun startPython(pythonHome: String, pythonPath: String, mainFile: String)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Get paths to Python assets
        val pythonHome = File(applicationInfo.dataDir, "files/python/${Build.SUPPORTED_ABIS[0]}").absolutePath
        val pythonPath = File(applicationInfo.dataDir, "files/python/${Build.SUPPORTED_ABIS[0]}/lib/python3.9").absolutePath +
                         ":" + File(applicationInfo.dataDir, "files/user_python").absolutePath
        val mainFile = "main.py" // Assuming main.py is in user_python directory

        Log.d("MainActivity", "Python Home: $pythonHome")
        Log.d("MainActivity", "Python Path: $pythonPath")
        Log.d("MainActivity", "Main File: $mainFile")

        // Start Python interpreter
        startPython(pythonHome, pythonPath, mainFile)

        setContent {
            MyDroidAppTheme {
                // A surface container using the 'background' color from the theme
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    Greeting("Android")
                }
            }
        }
    }
}

@Composable
fun Greeting(name: String, modifier: Modifier = Modifier) {
    Text(
        text = "Hello $name!",
        modifier = modifier
    )
}

@Preview(showBackground = true)
@Composable
fun GreetingPreview() {
    MyDroidAppTheme {
        Greeting("Android")
    }
}
