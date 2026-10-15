package org.titanv80.app;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.net.HttpURLConnection;
import java.net.URL;

public class MainActivity extends AppCompatActivity {
    private static final String DASHBOARD_URL = "http://127.0.0.1:5000/";
    private final Handler handler = new Handler(Looper.getMainLooper());
    private WebView webView;
    private volatile boolean destroyed = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webview);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMediaPlaybackRequiresUserGesture(false);
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient());

        startPythonServer();
    }

    private void startPythonServer() {
        new Thread(() -> {
            PyObject module = null;
            try {
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(getApplicationContext()));
                }
                Python python = Python.getInstance();
                module = python.getModule("android_main");
                // Persist TITAN state under the app-private files/JJJ directory.
                module.callAttr("start_server", getFilesDir().getAbsolutePath());
            } catch (Exception e) {
                final String message = e.getClass().getSimpleName() + ": " + String.valueOf(e.getMessage());
                handler.post(() -> showError("موتور TITAN اجرا نشد", message));
                return;
            }

            boolean ready = false;
            String lastError = "سرور محلی هنوز پاسخ نمی‌دهد.";
            for (int i = 0; i < 45 && !destroyed; i++) {
                HttpURLConnection connection = null;
                try {
                    connection = (HttpURLConnection) new URL(DASHBOARD_URL).openConnection();
                    connection.setConnectTimeout(900);
                    connection.setReadTimeout(1200);
                    connection.setUseCaches(false);
                    int code = connection.getResponseCode();
                    if (code >= 200) {
                        ready = true;
                        break;
                    }
                    lastError = "HTTP " + code;
                } catch (Exception e) {
                    lastError = e.getClass().getSimpleName() + ": " + String.valueOf(e.getMessage());
                } finally {
                    if (connection != null) connection.disconnect();
                }
                try {
                    Thread.sleep(600);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }

            final boolean serverReady = ready;
            final String failure = lastError;
            handler.post(() -> {
                if (destroyed || webView == null) return;
                if (serverReady) {
                    webView.loadUrl(DASHBOARD_URL);
                } else {
                    showError("داشبورد محلی آماده نشد", failure);
                }
            });
        }, "tai-python-engine").start();
    }

    private void showError(String title, String detail) {
        if (webView == null || destroyed) {
            Toast.makeText(this, title + ": " + detail, Toast.LENGTH_LONG).show();
            return;
        }
        String safeTitle = escapeHtml(title);
        String safeDetail = escapeHtml(detail);
        String html = "<!doctype html><html lang='fa' dir='rtl'><meta charset='utf-8'>" +
                "<meta name='viewport' content='width=device-width,initial-scale=1'>" +
                "<body style='margin:0;background:#020617;color:#e2e8f0;font:16px sans-serif;padding:28px'>" +
                "<h2 style='color:#38bdf8'>⚡ TAI — TITAN PRO V80</h2><h3>" + safeTitle + "</h3>" +
                "<pre style='white-space:pre-wrap;background:#0f172a;border-radius:12px;padding:14px'>" +
                safeDetail + "</pre><p>برنامه را ببندید و دوباره باز کنید. این پیام به‌جای صفحه سفید نمایش داده می‌شود.</p>" +
                "</body></html>";
        webView.loadDataWithBaseURL("http://127.0.0.1/", html, "text/html", "UTF-8", null);
    }

    private String escapeHtml(String value) {
        if (value == null) return "";
        return value.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace("\"", "&quot;");
    }

    @Override
    protected void onDestroy() {
        destroyed = true;
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
