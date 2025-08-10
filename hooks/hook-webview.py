"""
PyInstaller hook for webview package to ensure all necessary dependencies are included.
"""

from PyInstaller.utils.hooks import collect_all, collect_data_files
import os

# Collect all webview related modules
datas, binaries, hiddenimports = collect_all('webview')

# Add specific hidden imports that pywebview needs
hiddenimports += [
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'webview.platforms.cef',
    'webview.js',
    'webview.js.api',
    'webview.util',
    'webview.menu',
    'webview.window',
    'clr',  # pythonnet for EdgeChromium
]

# Collect WebView2 DLLs from webview lib directory
webview_lib_files = collect_data_files('webview', includes=['lib/*.dll', 'lib/*.json'])
datas.extend(webview_lib_files)

# Add Windows-specific imports
import sys
if sys.platform == 'win32':
    hiddenimports += [
        'pythonnet',
        'System',
        'System.Threading',
        'System.Windows.Forms',
        'Microsoft.Web.WebView2.Core',
        'Microsoft.Web.WebView2.WinForms',
    ]