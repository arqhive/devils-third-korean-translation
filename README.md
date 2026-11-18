# 데빌즈 서드 (Wii U) 한글 패치

*Devil's Third* (Wii U, 일본판 `ADNJ`) 비공식 한국어 팬 패치입니다.
일본판(『デビルズサード』) 게임에 적용하며, 번역은 영어 자막을 기준으로 했습니다.

**제작: arqhive** · **최신 버전: [v1.0f](../../releases/tag/v1.0f)**

- 솔로 플레이의 자막, 임무 목표, 메뉴, 설명문, 수집품 설명, 팁을 한글화했습니다.
- 자막과 메뉴에 한글 글꼴(넥슨 워헤이븐)을 넣었습니다.
- 온라인 멀티플레이 전용 문구는 번역하지 않았습니다.
- 패처는 가지고 있는 일본판 게임 파일에서 한글판 파일을 만듭니다. 원본 파일은 바뀌지 않습니다.

> 이 저장소에는 **게임 데이터(게임 파일, 추출한 원문 대사, 원본 그래픽, 스크린샷)가 들어 있지 않습니다.**
> 패치를 적용하려면 본인이 소유한 게임에서 직접 덤프한 원본이 필요합니다.

## 사용자용: 패치 적용

### 준비물

- 일본판 「デビルズサード」(타이틀 ID `0005000010138F00`)의 복호화된 게임 파일.
  `content\DevilsThirdGame\CookedWiiU` 폴더에 `Coalesced_JPN.bin` 등이 있어야 합니다. 북미판(*Devil's Third*)에는 적용할 수 없습니다.
- Windows 10 이상. 따로 설치할 것은 없습니다.
- Wii U 실기: Aroma와 SDCafiine 플러그인, SD 카드. 또는 Cemu 2.6.

### 적용 방법

1. [릴리즈 페이지](../../releases/latest)에서 `ADNJ_KPatch_v<버전>.zip`을 받아 압축을 풉니다.
2. 게임 폴더(`content` 폴더가 들어 있는 폴더)를 `패치하기.bat` 위에 끌어다 놓습니다. 그냥 실행하면 경로를 묻습니다.
3. 패처 폴더의 `출력` 폴더에 결과가 생깁니다.
   - Wii U 실기: `출력\sdcafiine` 안의 내용을 SD 카드 `wiiu\sdcafiine\`에 복사하고, SDCafiine을 켠 상태로 게임을 실행합니다.
   - Cemu: `출력\cemu\DevilsThirdKR` 폴더를 Cemu의 `graphicPacks` 폴더에 넣고, 그래픽팩 설정에서 Devil's Third → Mods → Korean Patch를 켭니다.

### 실행 환경

- **확인함**: Wii U 실기(Aroma SDCafiine), Cemu 2.6.

### 알려진 문제

- 일부 그림 속 글씨는 일본어 그대로입니다.

## 개발자용

- 번역문: [`work/translation/`](work/translation)에 한국어 번역문(키 → 번역)만 들어 있습니다.
- 도구: [`tools/`](tools)에 분석·추출·글꼴·빌드·검사 도구 소스가 있고, [`patcher/`](patcher)와 [`tools/make_patcher.py`](tools/make_patcher.py)가 배포 패처입니다(Python 3.13, numpy, Pillow, fontTools, pycryptodome, etcpak, freetype-py).
- 일본어 원문 추출본, 글꼴 파일, 작업 상태 기록은 게임 데이터이거나 작업용이라 넣지 않았습니다. 그래서 이 저장소만으로는 바로 빌드되지 않고, 원본 게임 파일에서 추출부터 다시 해야 합니다.

## 변경 내역

전체 내역은 [`CHANGELOG.md`](CHANGELOG.md)에 있습니다.

## 크레딧·라이선스

- 이 저장소의 도구 코드, 한국어 번역문, 문서: [MIT License](LICENSE) (© 2026 arqhive).
- 글꼴: 넥슨 워헤이븐(넥슨). 글꼴 파일은 저장소에 포함하지 않습니다.
- 패처 동봉 도구: Python 3.13(PSF), pycryptodome(BSD), xdelta3 3.1.0(Apache-2.0). 라이선스는 [`patcher/licenses/`](patcher/licenses)에 있습니다.

## 면책

비공식 팬 번역이며 Nintendo, Valhalla Game Studios와 관련이 없습니다. 「デビルズサード」 관련 상표·저작권은 각 권리자에게 있습니다.
패치를 적용한 게임 파일의 배포를 금지합니다.
