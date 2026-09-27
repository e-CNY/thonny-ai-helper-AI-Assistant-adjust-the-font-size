"""
thonny‑ai‑helper AI助手调整字体大小
同目录模式，脚本和ai_helper.py放一起；自动备份ai_helper.py.bak
功能：Ctrl+鼠标滚轮缩放AI聊天字体，字号持久保存
视频演示：https://www.bilibili.com/video/BV1Khat6BEsm
使用说明：https://github.com/e-CNY/thonny-ai-helper-AI-Assistant-adjust-the-font-size/blob/main/README.md

"""
import os
import sys
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
FILE_PATH = os.path.join(SCRIPT_DIR, "ai_helper.py")

# 在 self._text_area.grid(...) 之后插入，_setup_text_area_tags之前
INSERT_INIT_CODE = '''
        # ========== PATCH:独立AI聊天字体、滚轮绑定 ==========
        self._ai_base_font = tk.font.nametofont("TkDefaultFont").copy()
        # 读取配置，None时兜底默认10，防止tk报错
        saved_size = get_workbench().get_option("ai_assistant.chat_font_size")
        if saved_size is None or not isinstance(saved_size, int):
            saved_size = 10
        self._ai_base_font.configure(size=saved_size)
        self._text_area.configure(font=self._ai_base_font)
        # Ctrl+鼠标滚轮绑定 Windows/Linux
        self._text_area.bind("<Control-MouseWheel>", self._on_zoom_mousewheel)
        self._text_area.bind("<Control-Button-4>", self._on_zoom_mousewheel)
        self._text_area.bind("<Control-Button-5>", self._on_zoom_mousewheel)
'''

# 追加到AIAssistantView类末尾缩放方法
APPEND_METHODS = '''
    # ========== PATCH新增：Ctrl+滚轮缩放字体 ==========
    def _on_zoom_mousewheel(self, event):
        """Ctrl+鼠标滚轮调整AI聊天面板字号，仅作用本面板，自动保存配置"""
        current_size = self._ai_base_font.cget("size")
        if hasattr(event, "delta"):
            delta = event.delta
        elif event.num == 4:
            delta = 120
        elif event.num == 5:
            delta = -120
        else:
            return
        step = 1
        if delta > 0:
            new_size = current_size + step
        else:
            new_size = max(6, current_size - step)
        self._ai_base_font.configure(size=new_size)
        get_workbench().set_option("ai_assistant.chat_font_size", new_size)
        self._setup_text_area_tags()
'''

OLD_SETUP_LINE = 'default_font = tk.font.nametofont("TkDefaultFont")'
NEW_SETUP_LINE = 'default_font = self._ai_base_font'

OLD_CODE_FONT_LINE = 'code_font_size = get_workbench().get_option("view.editor_font_size") -1'
NEW_CODE_FONT_LINE = 'code_font_size = self._ai_base_font.cget("size") - 1'

ADD_CONFIG_LINE = '    wb.set_default("ai_assistant.chat_font_size", 10)'


def patch_file(file_path):
    if not os.path.isfile(file_path):
        print(f"❌找不到文件：{file_path}")
        print("请将本脚本与 ai_helper.py 放在同一个文件夹！")
        return False

    bak_path = file_path + ".bak"
    with open(file_path, "r", encoding="utf-8") as f:
        src = f.read()

    #备份
    if not os.path.exists(bak_path):
        with open(bak_path, "w", encoding="utf-8") as f:
            f.write(src)
        print(f"✅已备份原始文件：{bak_path}")
    else:
        print(f"ℹ️备份文件已存在，跳过备份：{bak_path}")

    # 插入字体初始化（正确位置：grid之后，_setup_text_area_tags之前）
    if "# ========== PATCH:独立AI聊天字体" not in src:
        src = re.sub(
            r'(self\._text_area\.grid\(row=0, column=0, sticky="nsew"\)\s*\n)',
            r"\1" + INSERT_INIT_CODE,
            src
        )
        print("✅已插入字体初始化与滚轮绑定（带None兜底）")
    else:
        print("ℹ️init补丁已经存在，跳过")

    #追加缩放方法
    if "def _on_zoom_mousewheel" not in src:
        src = re.sub(
            r"(class AIAssistantView\(ttk\.Frame\):.*?)(?=^def |^# --- )",
            r"\1" + APPEND_METHODS,
            src,
            flags=re.DOTALL | re.MULTILINE
        )
        print("✅追加 _on_zoom_mousewheel 缩放方法")
    else:
        print("ℹ️缩放方法已存在，跳过")

    #修改_setup_text_area_tags default_font
    if OLD_SETUP_LINE in src:
        src = src.replace(OLD_SETUP_LINE, NEW_SETUP_LINE)
        print("✅修改setup标签函数，使用self._ai_base_font")
    else:
        print("ℹ️default_font已修改，跳过")

    #修改代码块字号跟随AI字体
    if OLD_CODE_FONT_LINE in src:
        src = src.replace(OLD_CODE_FONT_LINE, NEW_CODE_FONT_LINE)
        print("✅代码块字号跟随AI聊天字体")
    else:
        print("ℹ️code_font_size已修改，跳过")

    #注入load_plugin默认配置
    if 'wb.set_default("ai_assistant.chat_font_size"' not in src:
        src = re.sub(
            r'(wb\.set_default\("ai_assistant\.model", ""\)\s*\n)',
            r"\1" + ADD_CONFIG_LINE + "\n",
            src
        )
        print("✅添加chat_font_size默认配置项")
    else:
        print("ℹ️配置项已存在，跳过")

    #写回文件
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(src)

    print(f"\n✅全部补丁写入完成 → {file_path}")
    print("\n❗完全关闭Thonny后再重新打开！")
    print("使用：鼠标放在AI聊天区域，按住 Ctrl + 鼠标滚轮缩放文字，设置自动保存。")
    return True


def main():
    print("===== thonny‑ai‑helper【最终修复版补丁】 =====")
    print(f"目标文件路径: {FILE_PATH}\n")
    try:
        ok = patch_file(FILE_PATH)
        if not ok:
            print("\n❌操作失败！")
    except Exception as e:
        print(f"\n❌异常：{repr(e)}")
        print("提示：确认Thonny完全退出，没有占用ai_helper.py文件。")
    input("\n按回车键关闭窗口...")


if __name__ == "__main__":
    main()
