# -*- coding: utf-8 -*-
from pynput import keyboard
import time
import sys
import subprocess
import requests
import json
import pyperclip
import uiautomation as auto
from uiautomation import UIAutomationInitializerInThread   # 新增导入
import threading

# ===========配置区============
API_KEY = '请到硅基流动官网申请'          # 请替换为你的apikey
API_URL = 'https://api.siliconflow.cn/v1/chat/completions'
MODEL = 'deepseek-ai/DeepSeek-V3'        # 模型可自行修改
SYSTEM_PROMPT = "[此处是提示词]"         
PREFIX = "[微信自动回复机器人] "           # 自动回复前缀
WAIT_Delay = 2                           # 检查新消息的间隔(s)
is_memory = True                          # 是否开启记忆功能
if is_memory:
    MAX_HISTORY_ROUNDS = 10                # 保留最近10轮对话
# =============================

msglist = None
is_running = False
last_msg = None
msg_his = [{"role": "system", "content": SYSTEM_PROMPT}]
mnt_run = None   # 改为 mnt_run，与后面线程变量一致

def set_clipboard_text(text):
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        print(f"[错误] 设置剪贴板失败: {e}")
        return False

def get_reply(history):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    # 这个请求头是针对硅基流动api的，如果你使用其他api，请根据需要修改
    payload = {
        'model': MODEL,
        'messages': history,
        'stream': False
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        reply = data['choices'][0]['message']['content']
        return reply.strip()
    except Exception as e:
        print(f"[API错误] {e}")
        return None

def trim_history(history):
    if not is_memory:
        if len(history) <= MAX_HISTORY_ROUNDS * 2 + 1:
            return history
        system = [history[0]]
        recent = history[-(MAX_HISTORY_ROUNDS * 2):]
        return system + recent
    return history

def find_msglist(control):
    while control:
        if control.AutomationId == 'chat_message_list': 
            return control
        # 模糊一下，防止不适配不同版本WX
        if control.AutomationId and 'chat_message_list' in control.AutomationId and 'chat_bubble_item_view' not in control.AutomationId:
            return control
        control = control.GetParentControl()
    return None

def get_latest_message_text(list_container, my_prefix):
    items = [child for child in list_container.GetChildren() if child.ControlType == auto.ControlType.ListItemControl]
    if not items:
        return None
    last_item = items[-1]
    texts = []
    def collect_text(ctrl):
        if ctrl.Name and ctrl.Name.strip():
            texts.append(ctrl.Name.strip())
        for child in ctrl.GetChildren():
            collect_text(child)
    collect_text(last_item)
    full_text = ' '.join(texts)
    if full_text and not full_text.startswith(my_prefix):
        return full_text
    return None

def monitor_loop():
    global last_msg, msg_his, is_running
    print("[log] 开始监控新消息...")
    # 在线程内初始化COM，确保整个循环期间COM可用
    with UIAutomationInitializerInThread():
        while is_running:
            try:
                if msglist is None:
                    print("[log] 消息列表容器未设置，请先按 F1 定位。")
                    is_running = False
                    break

                current_msg = get_latest_message_text(msglist, PREFIX)
                if current_msg and current_msg != last_msg:
                    print(f"\n[log] 检测到新消息: {current_msg}")
                    msg_his.append({"role": "user", "content": current_msg})
                    msg_his = trim_history(msg_his)

                    reply = get_reply(msg_his)
                    if reply:
                        print(f"[log] 生成回复: {reply}")
                        set_clipboard_text(reply)
                        # 模拟粘贴，直接输入会被微信云控（哭
                        with keyboard.Controller() as kb:
                            kb.press(keyboard.Key.ctrl)
                            kb.press('v')
                            kb.release('v')
                            kb.release(keyboard.Key.ctrl)

                        if is_memory:
                            msg_his.append({"role": "assistant", "content": reply})
                        last_msg = current_msg 
                    else:
                        print("[log] 未能获取回复，跳过本轮。")
                else:
                    print(f"[log] 没有新消息，等待 {WAIT_Delay} 秒...")
                time.sleep(WAIT_Delay)
            except Exception as e:
                print(f"[log] 异常: {e}")
                time.sleep(WAIT_Delay)
    print("[log] 监控已停止。")

def on_press(key):
    global msglist, is_running, last_msg, msg_his, mnt_run   # 修正为 mnt_run
    try:
        if key == keyboard.Key.f1:
            # F1 定位消息列表容器，需要COM初始化
            with UIAutomationInitializerInThread():
                x, y = auto.GetCursorPos()
                print(f"\n[log] 鼠标位置: ({x}, {y})")
                ctrl = auto.ControlFromPoint(x, y)
                if not ctrl or not ctrl.Exists():
                    print("无法获取控件!")
                    return
                container = find_msglist(ctrl)
                if container:
                    msglist = container
                    print("成功定位到消息列表容器！")
                    print(f"  容器 ClassName: {container.ClassName}")
                    print(f"  容器 AutomationId: {container.AutomationId}")
                    msg_his = [{"role": "system", "content": SYSTEM_PROMPT}]
                    print("已重置对话历史。")
                    last_msg = get_latest_message_text(container, PREFIX)
                    if last_msg:
                        print(f"当前最新消息: {last_msg}")
                    else:
                        print("当前聊天区域没有消息或无法提取")
                else:
                    print("未找到消息列表容器，请确保鼠标位于消息项上。")

        elif key == keyboard.Key.f2:
            if is_running:
                print("[log] 监控已经在运行中。")
            else:
                if msglist is None:
                    print("[log] 请先按 F1 定位消息列表容器。")
                    return
                is_running = True
                mnt_run = threading.Thread(target=monitor_loop, daemon=True)
                mnt_run.start()   # 使用 mnt_run.start()

        elif key == keyboard.Key.f3:
            if is_running:
                is_running = False
                print("[F3] 正在停止监控...")
            else:
                print("[F3] 监控未运行。")

    except Exception as e:
        print(f"[错误] {e}")

def main():
    print("微信自动回复已启动！")
    print("按F1定位消息列表容器，按F2开始监控新消息，按F3退出")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()
