"""번역 범위 규칙(2026-11-06 사용자 「멀티는 빼기」).

scope: 'solo' = 번역, 'mp' = 멀티 전용이라 뺌, 'engine' = 엔진 기본 문구라 뺌, 'data' = 화면 글이 아닌 자료(번역 금지)
근거: 무비가 실린 패키지. 솔로 메뉴 패키지(D3Start·D3GameOutGameContent_SF·SP_GAME_P·DevilsThirdGame)에 없는
무비(DsrManual·DsrLoadout·DsrChatWindow·Clan·Lobby·Mail·Emblem 등)는 멀티 전용.
"""

# 파일 통째로 멀티
MP_FILES = {
    'DT_Manual',                 # 게임 안 설명서: DsrManual 무비는 멀티 패키지에만 있음
    'DT_UI_Labels_Clan', 'DT_UI_Labels_CharaMake', 'DT_UI_Labels_PlayerNotice', 'DT_UI_Labels_MapEdit',
    'DT_UI_Labels_LoadOut', 'DT_UI_Labels_PlayerMenus', 'DT_Multiplay_Generic', 'DT_Multiplay_Voices',
    'DT_DSR_Map', 'DT_Templates', 'E_Shop', 'Shop', 'DT_Weapons_SPW',
}
MP_FILE_PREFIX = ('DT_MultiplayGame_',)

# 파일 안 구역 단위로 멀티
MP_SECTIONS = {
    # 'DT_Tips' Multi·Multi_Games·Multi_MapEdit 는 11/18 솔로로 옮김: 솔로 로딩 화면에도 나옴(사용자 실기 캡처 System_08)
    'DT_Game_Generic': {'EmblemCategory', 'EmblemPattern', 'Event_Chicken'},
    'DT_UI_Labels': {'AreaCustomize_Menus', 'Chat_Detail', 'Chat_Labels', 'ClassName_Labels', 'DsrBasePool_Labels',
                     'EmblemEditor_Labels', 'Exchange_Labels', 'Friend_Menus', 'GameMode_Descriptions',
                     'GameMode_Labels', 'ListingRoom_Labels', 'Lobby_Labels', 'Mail_Detail', 'Mail_Labels',
                     'MultiResult_Labels', 'MyPage_Labels', 'Registration_Detail', 'Registration_Labels',
                     'Stats_Orders'},
    'DT_UI_Labels_Ranking': {'Params_Multi'},
    'DT_Weapons': {'Attachments', 'Attachments_Descriptions', 'SpecialArms', 'SpecialArms_Descriptions'},
}

# 화면 글이 아닌 자료
DATA_SECTIONS = {
    'DevilsThirdGameResource': {'Kana'},   # 가나 변환표(이름 입력용)
}


# 엔진 기본 문구(개발·네트워크 오류·PC 안내) — 2026-11-06 사용자 「엔진도 빼기」
ENGINE_FILES = {'Core', 'Engine', 'IpDrv', 'Launch', 'Startup', 'subtitles', 'editormaptemplates',
                'onlinesubsystemgamespy'}


def scope_of(file, section):
    if section in DATA_SECTIONS.get(file, ()):
        return 'data'
    if file in ENGINE_FILES:
        return 'engine'
    if file in MP_FILES or file.startswith(MP_FILE_PREFIX):
        return 'mp'
    if section in MP_SECTIONS.get(file, ()):
        return 'mp'
    return 'solo'
