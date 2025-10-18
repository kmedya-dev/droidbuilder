package com.example.myapp

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import java.io.File
import kotlin.concurrent.thread
import android.os.Build
import java.io.FileOutputStream
import java.io.InputStream

class MainActivity : AppCompatActivity() {

    companion object {
        init {
            System.loadLibrary("python_bootstrap")
        }
    }

    private external fun startPython(pythonHome: String, pythonPath: String, argv: Array<String>)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val outputTextView: TextView = findViewById(R.id.output_text)
        outputTextView.text = "Starting Python..."

        thread {
            val pythonHome = extractAssets()
            if (pythonHome == null) {
                runOnUiThread {
                    outputTextView.text = "Failed to extract assets."
                }
                return@thread
            }

            val libDir = pythonHome.resolve("lib")
            val pythonLibDir = libDir.listFiles()?.find { it.name.startsWith("python") }
            if (pythonLibDir == null) {
                runOnUiThread {
                    outputTextView.text = "Could not find python lib directory."
                }
                return@thread
            }
            val pythonVersion = pythonLibDir.name.substring("python".length)

            val pythonPath = listOf(
                pythonLibDir.absolutePath,
                pythonLibDir.resolve("lib-dynload").absolutePath,
                filesDir.resolve("user_python").absolutePath
            ).joinToString(":")
            val mainFile = "main.py"

            startPython(pythonHome.absolutePath, pythonPath, arrayOf(mainFile))

            runOnUiThread {
                outputTextView.text = "Python script finished."
            }
        }
    }

    private fun extractAssets(): File? {
        val pythonHome = File(filesDir, "python")
        try {
            if (pythonHome.exists()) {
                pythonHome.deleteRecursively()
            }
            pythonHome.mkdirs()

            val arch = Build.SUPPORTED_ABIS[0]
            extractAssetDir("python/$arch", pythonHome)
            return pythonHome
        } catch (e: Exception) {
            e.printStackTrace()
            return null
        }
    }

    private fun extractAssetDir(path: String, targetDir: File) {
        assets.list(path)?.forEach { asset ->
            val assetPath = "$path/$asset"
            val targetFile = File(targetDir, asset)
            try {
                assets.open(assetPath).use { inputStream ->
                    targetFile.outputStream().use { outputStream ->
                        inputStream.copyTo(outputStream)
                    }
                }
            } catch (e: java.io.FileNotFoundException) {
                targetFile.mkdirs()
                extractAssetDir(assetPath, targetFile)
            }
        }
    }
}
