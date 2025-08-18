from telethon import TelegramClient, events 
import asyncio 
 
api_id = 29181790 
api_hash = '94ab5d4154e81a5db294fe0dcd2dcb1b' 
bot_token = '8255949138:AAE_hmsWP3iLuIpiW_nb_GBuS_u_PIPbjgA'  # غيّر التوكن فورًا! 
 
sessions = ['session1', 'session2', 'session3', 'session4', 'session5', 'session6'] 
clients = [TelegramClient(s, api_id, api_hash) for s in sessions] 
bot = TelegramClient('bot_session', api_id, api_hash) 
 
# قائمة لتتبع المستخدمين الذين ينتظرون بيانات التصويت منهم 
waiting_for_vote = set() 
 
async def start_clients(): 
    await asyncio.gather(*[client.start() for client in clients]) 
 
async def stop_clients(): 
    await asyncio.gather(*[client.disconnect() for client in clients]) 
 
@bot.on(events.NewMessage(pattern='/start')) 
async def start(event): 
    await event.respond('مرحباً! أرسل /vote لبدء التصويت.') 
 
@bot.on(events.NewMessage(pattern='/vote')) 
async def vote_handler(event): 
    user_id = event.sender_id 
    if user_id in waiting_for_vote: 
        await event.respond('لقد طلبت بالفعل التصويت، يرجى إرسال البيانات أو انتظر انتهاء العملية السابقة.') 
        return 
    waiting_for_vote.add(user_id) 
    await event.respond('يرجى إرسال الرابط والكلمة والتأخير مفصولة بفواصل (مثال: رابط,كلمة,5)') 
 
@bot.on(events.NewMessage) 
async def receive_data(event): 
    user_id = event.sender_id 
    if user_id not in waiting_for_vote: 
        return 
 
    try: 
        parts = event.text.split(',') 
        if len(parts) != 3: 
            await event.respond('تنسيق غير صحيح، حاول مرة أخرى.') 
            return 
 
        link = parts[0].strip() 
        vote_word = parts[1].strip() 
        delay = float(parts[2].strip()) 
 
        await event.respond(f'جارٍ إرسال التصويت على {link} كل {delay} ثانية...') 
 
        await start_clients() 
 
        # التصويت 5 مرات كمثال (أو غيّر الرقم حسب حاجتك) 
        for i in range(5): 
            for client in clients: 
                try: 
                    await client.send_message(link, vote_word) 
                except Exception as e: 
                    await event.respond(f'فشل إرسال التصويت: {e}') 
            await asyncio.sleep(delay) 
 
        await event.respond('تمت عملية التصويت!') 
        await stop_clients() 
 
    except Exception as e: 
        await event.respond(f'حدث خطأ: {e}') 
    finally: 
        waiting_for_vote.discard(user_id) 
 
async def main(): 
    print("Starting bot...") 
    await bot.start(bot_token=bot_token) 
    print("Bot started successfully") 
    await bot.run_until_disconnected() 
 
if name == '__main__': 
    asyncio.run(main())
