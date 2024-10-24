import os
import spotipy

from spotipy import SpotifyException, SpotifyClientCredentials
from aiogram import types, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

router = Router()


class SearchArtist(StatesGroup):
    artist_name = State()


class SearchTrack(StatesGroup):
    track_name = State()


class SearchAlbum(StatesGroup):
    album_name = State()


class SearchGenre(StatesGroup):
    genre_name = State()
    amount_tracks = State()


class Recommend(StatesGroup):
    track_name = State()
    artist_name = State()


class SearchEra(StatesGroup):
    era_name = State()


@router.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.reply("Этот бот может рассазать какая музыка сейчас находится в чартах, найти рекоммендации "
                        "специально под Ваш вкус, сможет рассказать Вам про альбом или исполнителя, "
                        "которыий Вас интересует и найти музыку Вашего любимого жанра.\n\n<b>Подробнее здесь: /help</b>",
                        parse_mode="html")


@router.message(Command('help'))
async def send_help(message: types.Message):
    await message.reply("Методы доступные Вам:\n"
                        "/search_artist - найдет исполнителя, который Вас интересует и расскажет про него.\n"
                        "/search_track - найдет информацию о треке по его названию.\n"
                        "/search_album - найдет альбом по названию и даст ссылки на все треки, которые включены в него.\n"
                        "/search_by_genre - найдет столько треков определенного жанра, сколько Вам нужно.\n"
                        "/search_similar_tracks - даст рекоммендации по названию трека.\n"
                        "/search_similar_by_artist - даст рекоммендации по псевдониму исполнителя.\n"
                        "/new_releases - найдет лучшие новые релизы, которые сейчас играют по всему миру.\n"
                        "/search_by_era - найдет треки любой эпохи.")


@router.message(Command('search_artist'))
async def search_artist(message: types.Message, state: FSMContext):
    await state.set_state(SearchArtist.artist_name)
    await message.reply("Введите псевдоним исполнителя:")


@router.message(Command('search_track'))
async def search_track(message: types.Message, state: FSMContext):
    await state.set_state(SearchTrack.track_name)
    await message.reply("Введите название трека:")


@router.message(Command('search_album'))
async def search_album(message: types.Message, state: FSMContext):
    await state.set_state(SearchAlbum.album_name)
    await message.reply("Введите название альбома:")


@router.message(Command('search_by_genre'))
async def search_album(message: types.Message, state: FSMContext):
    await state.set_state(SearchGenre.amount_tracks)
    await message.reply("Введите сколько треков вы хотите узнать")

@router.message(Command('search_similar_tracks'))
async def search_similar_tracks(message: types.Message, state: FSMContext):
    await state.set_state(Recommend.track_name)
    await message.reply("Введите название трека, для которого вы хотите найти рекоммендации")


@router.message(Command('search_similar_by_artist'))
async def search_similar_by_artist(message: types.Message, state: FSMContext):
    await state.set_state(Recommend.artist_name)
    await message.reply("Введите название исполнителя, для которого вы хотите найти реккомендации")


@router.message(Command('new_releases'))
async def get_new_releases_tracks(message: types.Message, state: FSMContext):
    country_code = None

    try:
        new_releases = sp.new_releases(country=country_code, limit=10)

        if new_releases['albums']['items']:
            response = "Трендовые треки:\n"
            for idx, album in enumerate(new_releases['albums']['items'], start=1):
                album_name = album['name']
                album_url = album['external_urls']['spotify']
                artists = ', '.join([artist['name'] for artist in album['artists']])
                response += f"\n{idx}: {album_name} by {artists} ({album_url})\n"
            await message.reply(response)
        else:
            await message.reply("Ничего не найдено. Попробуйте снова.")
        await state.clear()

    except SpotifyException as e:
        print(e)
        await message.answer('К сожалению произошла ошибка при получении трендов :(')


@router.message(Command('search_by_era'))
async def search_by_era(message: types.Message, state: FSMContext):
    await state.set_state(SearchEra.era_name)
    await message.reply("Введите эпоху или временной промежуток (например, '1980s', '1990-2000'):")


@router.message(Command('chart'))
async def get_spotify_chart(message: types.Message):
    try:
        playlist_id = '37i9dQZEVXbMDoHDwVN2tF'
        results = sp.playlist_items(playlist_id, limit=30)

        if results['items']:
            response = "Текущий чарт Spotify 'Top 30 Global':\n\n"
            for idx, item in enumerate(results['items'], start=1):
                track = item['track']
                track_name = track['name']
                track_artists = ', '.join([artist['name'] for artist in track['artists']])
                track_url = track['external_urls']['spotify']
                response += f"{idx}. {track_name} by {track_artists}\nСсылка: {track_url}\n\n"

            await message.reply(response)
        else:
            await message.reply("Не удалось получить чарт. Попробуйте позже.")
    except SpotifyException as e:
        print(e)
        await message.answer('Произошла ошибка при попытке получить чарт Spotify :(')



@router.message(SearchArtist.artist_name)
async def get_artist_info(message: types.Message, state: FSMContext):
    await state.update_data(artist_name=message.text.strip())

    data = await state.get_data()
    try:
        results = sp.search(q='artist:' + data['artist_name'], type='artist', limit=1)

        if results['artists']['items']:
            artist = results['artists']['items'][0]
            artist_name = artist['name']
            followers = artist['followers']['total']
            genres = ', '.join(artist['genres'])
            url = artist['external_urls']['spotify']

            response = (f"Артист: {artist_name}\n"
                        f"Количество подписчиков: {followers}\n"
                        f"Жанры: {genres}\n"
                        f"Ссылка на Spotify: {url}\n\n")


            top_tracks = sp.artist_top_tracks(artist['id'], country='US')['tracks']

            if top_tracks:
                response += "Популярные песни:\n"
                for idx, track in enumerate(top_tracks[:5], start=1):
                    track_name = track['name']
                    track_url = track['external_urls']['spotify']
                    response += f"{idx}. {track_name} - {track_url}\n"
            else:
                response += "Популярные треки не найдены."

            await message.answer(response)
        else:
            await message.answer("Исполнитель не найден. Попробуйте снова.")

        await state.clear()

    except SpotifyException as e:
        print(e)
        await message.answer('К сожалению произошла ошибка при поиске исполнителя :(')


@router.message(SearchTrack.track_name)
async def get_track_info(message: types.Message, state: FSMContext):
    await state.update_data(track_name=message.text.strip())

    data = await state.get_data()
    try:
        results = sp.search(q=data['track_name'], type='track', limit=1)

        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            response = (
                f"Название: {track['name']}\n"
                f"Исполнитель: {', '.join([artist['name'] for artist in track['artists']])}\n"
                f"Альбом: {track['album']['name']}\n"
                f"Дата релиза: {track['album']['release_date']}\n"
                f"Длительность: {round(track['duration_ms'] / (1000 * 60), 1)} м.\n"
                f"Ссылка на трек: {track['external_urls']['spotify']}"
            )
        else:
            response = "Трек не найден. Попробуйте снова."

        await message.answer(response)
        await state.clear()

    except SpotifyException as e:
        print(e)
        await message.answer('К сожалению произошла какая-то ошибка :(')


@router.message(SearchAlbum.album_name)
async def get_album_info(message: types.Message, state: FSMContext):
    await state.update_data(album_name=message.text.strip())

    data = await state.get_data()
    try:
        results = sp.search(q=data['album_name'], type='album', limit=1)

        if results['albums']['items']:
            album = results['albums']['items'][0]

            album_name = album['name']
            artists = ', '.join([artist['name'] for artist in album['artists']])
            release_date = album['release_date']
            total_tracks = album['total_tracks']
            album_url = album['external_urls']['spotify']

            response = (
                f"Название: {album_name}\n"
                f"Исполнитель: {artists}\n"
                f"Дата релиза: {release_date}\n"
                f"Количество треков: {total_tracks}\n"
                f"Ссылка на альбом: {album_url}\n\n"
            )


            tracks = sp.album_tracks(album['id'])['items']

            response += "Треки в альбоме:\n"
            for idx, track in enumerate(tracks):
                response += f"{idx + 1}. {track['name']} - {track['external_urls']['spotify']}\n"

        else:
            response = "Альбом не найден. Попробуйте снова."

        await message.answer(response)
        await state.clear()

    except SpotifyException as e:
        print(e)
        await message.answer('К сожалению произошла какая-то ошибка :(')


@router.message(SearchGenre.amount_tracks)
async def get_amount_tracks(message: types.Message, state: FSMContext):
    try:
        await state.update_data(amount_tracks=int(message.text.strip()))
        await state.set_state(SearchGenre.genre_name)
        await message.answer("Введите название жанра")
    except ValueError as e:
        print(e)
        await message.answer("Вы ввели не число :(, попробуйте заново ")


@router.message(SearchGenre.genre_name)
async def get_tracks_by_genre(message: types.Message, state: FSMContext):
    await state.update_data(genre_name=message.text.strip())
    data = await state.get_data()
    try:
        results = (sp.search(q='genre:"' + data['genre_name'] + '"',
                             type='track', limit=min(data['amount_tracks'], 30)))
        if results['tracks']['items']:
            response = "Треки в жанре " + data['genre_name'] + ":\n\n"
            for track in results['tracks']['items']:
                track_name = track['name']
                track_artists = ', '.join([artist['name'] for artist in track['artists']])
                track_url = track['external_urls']['spotify']

                response += f"- {track_name} by {track_artists}\nСсылка: {track_url}\n\n"
            await message.answer(response)
        else:
            await message.answer("Треки не найдены. Попробуйте снова.")

        await state.clear()
    except SpotifyException as e:
        print(e)
        await message.answer('К сожалению произошла какая-то ошибка :(')


@router.message(Recommend.track_name)
async def get_recommendation_track(message: types.Message, state: FSMContext):
    track_name = message.text.strip()
    await state.update_data(track_name=track_name)

    data = await state.get_data()

    try:
        results = sp.search(q=f'track:{data['track_name']}', type='track', limit=1)
        if results['tracks']['items']:
            track_id = results['tracks']['items'][0]['id']
            await message.reply(f"Выбранный трек: {data['track_name']}. Ищу рекомендации на его основе...")
            recommendations = sp.recommendations(seed_tracks=[track_id], limit=5)

            response = "Рекомендованные треки:\n"
            for track in recommendations['tracks']:
                track_name = track['name']
                track_artists = ', '.join([artist['name'] for artist in track['artists']])
                track_url = track['external_urls']['spotify']
                response += f"- {track_name} by {track_artists}\nСсылка: {track_url}\n\n"

            await message.answer(response)
        else:
            await message.reply("Трек не найден. Попробуйте другой запрос.")

        await state.clear()

    except SpotifyException as e:
        print(e)
        await message.reply("Произошла ошибка при поиске треков.")
        await state.clear()


@router.message(Recommend.artist_name)
async def get_recommendations_by_artist(message: types.Message, state: FSMContext):
    artist_name = message.text.strip()
    await state.update_data(artist_name=artist_name)

    data = await state.get_data()
    try:
        results = sp.search(q=f'artist:{data['artist_name']}', type='artist', limit=1)
        if results['artists']['items']:
            artist_id = results['artists']['items'][0]['id']
            await message.reply(f"Выбранный исполнитель: {data['artist_name']}. Ищу рекомендации на его основе...")
            recommendations = sp.recommendations(seed_artists=[artist_id], limit=7)

            response = "Рекомендованные треки:\n"
            for track in recommendations['tracks']:
                track_name = track['name']
                track_artists = ', '.join([artist['name'] for artist in track['artists']])
                track_url = track['external_urls']['spotify']
                response += f"- {track_name} by {track_artists}\nСсылка: {track_url}\n\n"

            await message.answer(response)
        else:
            await message.reply("Исполнитель не найден. Попробуйте другой запрос.")

        await state.clear()
    except SpotifyException as e:
        print(e)
        await message.reply("Произошла ошибка при поиске треков.")
        await state.clear()


@router.message(SearchEra.era_name)
async def get_tracks_by_era(message: types.Message, state: FSMContext):
    await state.update_data(era_name=message.text.strip().lower())

    era_data = await state.get_data()
    era = era_data['era_name']

    era_filters = {
        '1960s': '1960-1969',
        '1970s': '1970-1979',
        '1980s': '1980-1989',
        '1990s': '1990-1999',
        '2000s': '2000-2009',
        '2010s': '2010-2019',
    }

    if '-' in era:
        year_range = era
    elif era in era_filters:
        year_range = era_filters[era]
    else:
        await message.reply("Извините, я не понимаю эту эпоху. Попробуйте '1960s', '1970s',  '1980s', '1990s', '2000s', '2010s' или введите временной промежуток в формате '1990-2000'.")
        await state.clear()
        return

    try:
        results = sp.search(q=f'year:{year_range}', type='track', limit=10)

        if results['tracks']['items']:
            response = f"Треки из эпохи {era}:\n\n"
            for track in results['tracks']['items']:
                track_name = track['name']
                track_artists = ', '.join([artist['name'] for artist in track['artists']])
                track_url = track['external_urls']['spotify']

                response += f"- {track_name} by {track_artists}\nСсылка: {track_url}\n\n"
            await message.reply(response)
        else:
            await message.reply(f"Треки из эпохи {era} не найдены. Попробуйте другой временной промежуток.")

        await state.clear()

    except SpotifyException as e:
        print(e)
        await message.reply("Произошла ошибка при поиске треков.")
        await state.clear()

