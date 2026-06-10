import webview
import glob


class Api:
    def add(self, a, b):
        print("python")
        return a + b

    def pyprint(self, data):
        print(data)\


    def selectTiff(self):
        file_types = ('Image Files (*.tif)', 'All files (*.*)')
        result = window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=True, file_types=file_types)
        print(result)
        return result

    def selectFolder(self):
        result = window.create_file_dialog(webview.FOLDER_DIALOG)
        print(result)
        if (result != None and len(result) >= 1):
            return glob.glob(result[0]+"/"+"*.tif")
        else:
            return None

    def saveText(self, text):
        file_types = ('Text Files (*.txt)', 'All files (*.*)')
        result = window.create_file_dialog(
            webview.SAVE_DIALOG, file_types=file_types)
        with open(result, mode="w") as f:
            f.write(text)


api = Api()
window = webview.create_window(
    "My First App", url="web/index.html", js_api=api)
webview.start(http_server=True, debug=True)
