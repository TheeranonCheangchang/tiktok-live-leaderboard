import random
from flask import Flask, render_template
from flask_socketio import SocketIO
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, GiftEvent
import asyncio
import threading

# ตั้งค่า Web Server และ Socket
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# ใส่ชื่อ TikTok ของคุณ (ไม่ต้องมี @)
TIKTOK_USERNAME = "ki4uto"
client = TikTokLiveClient(unique_id=TIKTOK_USERNAME)

top_donors = {} # เก็บข้อมูลเพชรสะสม

# เมื่อเชื่อมต่อ TikTok สำเร็จ
@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print(f"เชื่อมต่อห้องไลฟ์ของ {event.room_id} สำเร็จแล้ว!")

# เมื่อมีคนส่งของขวัญ
@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    user_name = event.user.nickname
    gift_name = event.gift.name
    
    # ดึงราคาของขวัญ (เพชร) มาคำนวณเรท
    try:
        if hasattr(event.gift, 'info') and event.gift.info:
            diamonds = getattr(event.gift.info, 'diamond_count', 1)
        else:
            diamonds = getattr(event.gift, 'diamond_count', getattr(event.gift, 'diamonds', 1))
    except Exception:
        diamonds = 1
        
    # สะสมจำนวนเพชรสำหรับ Leaderboard
    if user_name not in top_donors:
        top_donors[user_name] = 0
    top_donors[user_name] += diamonds
    
    # ส่งข้อมูล Leaderboard (3 อันดับแรก) ไปที่ Frontend
    leaderboard = sorted(top_donors.items(), key=lambda x: x[1], reverse=True)[:3]
    socketio.emit('update_leaderboard', leaderboard)
        
    print(f"[{gift_name} - {diamonds} เพชร] {user_name} ได้สนับสนุนของขวัญ!")

# สร้าง Route สำหรับหน้าเว็บ
@app.route('/')
def index():
    return render_template('index.html')

# ฟังก์ชันสำหรับรัน TikTok Client แยก Thread
def run_tiktok():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client.run()

if __name__ == '__main__':
    # รัน TikTok Listener แยกออกไป เพื่อไม่ให้บล็อก Web Server
    threading.Thread(target=run_tiktok, daemon=True).start()
    # รัน Web Server ที่ Port 5000
    socketio.run(app, port=5000, allow_unsafe_werkzeug=True)