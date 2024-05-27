import asyncio
import os
import random
import opentele
from opentele.api import API, UseCurrentSession, CreateNewSession

from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeAudio, User, Channel

# Set the maximum number of messages to fetch per dialog
LIMIT = 350
# Set the maximum number of concurrent coroutines to run
MAX_CONCURRENT_COROUTINES = 5


# Function to get a list of all tdata directories
def get_tdata():
    curent_dir = os.path.join(os.getcwd(), "tdatas")
    tdata_list = [os.path.join(curent_dir, i) for i in os.listdir("./tdatas/") if "done_" not in i]
    return tdata_list


def callback(current, total):
    print('Downloaded', current, 'out of', total, 'bytes: {:.2%}'.format(current / total))


# Coroutine to process messages for a given dialog
async def process_dialog(dialog, tdata, client):
    messages_output = ""
    dialog_name = str(dialog.id)

    if not os.path.exists(os.path.join(tdata, dialog_name)):
        os.mkdir(os.path.join(tdata, dialog_name))

    try:
        entity = await client.get_entity(dialog.id)
        if isinstance(entity, User):
            # For user accounts, the username is stored in the 'username' attribute
            user_info = open(os.path.join(tdata, dialog_name, f"user_{dialog.id}_info.txt"), "w", encoding="utf-8", errors="ignore")
            user_info.write(f"{entity.username}, {entity.first_name}, {entity.id}, {entity.phone}")
            user_info.close()
    except Exception as exc:
        print(str(exc))

    # messages = [f"[{message.date}] {message.sender.first_name} ({message.sender.username}): {message.message}\n" async for message in client.iter_messages(dialog, limit=LIMIT)]
    # Iterate over messages in the dialog and download any media attachments
    messages = client.iter_messages(dialog, limit=LIMIT)
    async for message in messages:
        file_ = f"{os.path.join(tdata, dialog_name, str(message.sender.id) + '_' + message.date.strftime('%Y%m%d_%H%M%S'))}"

        if message.video:
            file_name = next((d.file_name for d in message.video.attributes if isinstance(d, DocumentAttributeFilename)), None)
            file_ = f"{file_}_{file_name}_.mp4"
            print(file_)
            await client.download_media(message, progress_callback=callback, file=file_)

        if message.document:
            is_audio = next((True for d in message.document.attributes if isinstance(d, DocumentAttributeAudio)), False)
            if is_audio:
                file_ = f"{file_}.mp3"
                print(file_)
                await client.download_media(message, progress_callback=callback, file=file_)

            file_name = next((d.file_name for d in message.document.attributes if isinstance(d, DocumentAttributeFilename)), None)
            if file_name and ".webp" not in file_name and ".webm" not in file_name and ".tgs" not in file_name and file_name:
                file_extension = file_name.split(".")[-1]
                # document1 = await client.download_media(message.media, file=f"{os.path.join(tdata, message.sender.first_name + '_' + file_name + '_' + message.date.strftime('%Y%m%d_%H%M%S'))}.{file_extension}")
                file_ = f"{file_}_{file_name}_.{file_extension}"
                print(file_)
                await client.download_media(message, progress_callback=callback, file=file_)

        if message.audio:
            file_ = f"{file_}.mp3"
            print(file_)
            await client.download_media(message, progress_callback=callback, file=file_)

        if message.photo:
            file_ = f"{file_}.jpg"
            print(file_)
            await client.download_media(message, progress_callback=callback, file=file_)

        messages_output += f"[{message.date}] {message.sender.first_name} ({message.sender.username}): {message.message}\n"

    # Get a list of all messages in the dialog and write them to a text file

    with open(f"{os.path.join(tdata, dialog_name, dialog_name)}.txt", "w", encoding="utf-8", errors="ignore") as f:
        f.write(messages_output)


async def main():
    tdatas = get_tdata()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_COROUTINES)
    tasks = []
    for tdata in tdatas:
        tdata_path = os.path.join(tdata, "tdata")
        if os.path.exists(tdata_path):
            tdesk = opentele.td.TDesktop(tdata_path)
            assert tdesk.isLoaded()

            try:
                # try:
                #     api = API.TelegramDesktop.Generate()
                #     client = await tdesk.ToTelethon(f"{os.path.basename(tdata)}.session", CreateNewSession, api)
                # except:
                #     client = await tdesk.ToTelethon(session=f"{os.path.basename(tdata)}.session", flag=UseCurrentSession)

                client = await tdesk.ToTelethon(session=f"{os.path.join(tdata, os.path.basename(tdata))}.session", flag=UseCurrentSession)

                await client.connect()
                await client.PrintSessions()

                dialogs = [dialog async for dialog in client.iter_dialogs() if not dialog.is_group and not dialog.is_channel]
                for dialog in dialogs:
                    async with semaphore:
                        tasks.append(asyncio.create_task(process_dialog(dialog, tdata, client)))

            except Exception as exc:
                print(str(exc))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
