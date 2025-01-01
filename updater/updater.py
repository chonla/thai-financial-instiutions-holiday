from enum import StrEnum
from datetime import datetime
from typing import Any, List, Dict, NamedTuple, IO
from requests import get
import json
import hashlib
import sys
import re
import humps


version_json_filename = "VERSION.json"
readme_filename = "README.md"


class Lang(StrEnum):
    TH = "th"
    EN = "en"


class Name(StrEnum):
    FULL = "full"
    ABBR = "abbr"


class Holiday(NamedTuple):
    date_stamp: str # YYYYMMDD
    day_of_week_index: int # Sun=0, ..., Sat=6
    day_of_week_th: str
    day_of_week_en: str
    day_of_week_abbr_en: str
    day_of_week_abbr_th: str
    day: int # Day of month
    month_index: int # Jan=0, ..., Dec=11
    month_th: str
    month_abbr_th: str
    month_en: str
    month_abbr_en: str
    year_ce: int # In Christian era
    year_be: int # In Buddhist era
    description_th: str
    description_en: str


class HolidayInYear(NamedTuple):
    year_ce: int
    year_be: int
    data: List[Holiday]


class HolidayDetail(NamedTuple):
    day_of_week_index: int # Sun=0, ..., Sat=6
    day_of_week_th: str
    day_of_week_en: str
    day_of_week_abbr_en: str
    day_of_week_abbr_th: str
    day: int # Day of month
    month_index: int # Jan=0, ..., Dec=11
    month_th: str
    month_abbr_th: str
    month_en: str
    month_abbr_en: str
    year_ce: int # In Christian era
    year_be: int # In Buddhist era
    description: str


class BOTHoliday(NamedTuple):
    # Holiday Data from Bank of Thailand
    date: str
    month: str
    year: str
    description: str


def get_holiday_url(lang: Lang = Lang.EN, year: int = 2024):
    base_url = f"https://www.bot.or.th/content/bot/{lang}/financial-institutions-holiday/jcr:content/root/container/holidaycalendar"
    lang_suffix = "_copy" if lang == Lang.TH else ""
    year_model = f"{year + 543}" if lang == Lang.TH else f"{year}"
    
    return f"{base_url}{lang_suffix}.model.{year_model}.json"


def get_holiday(year: int = 2024) -> List[Dict]:
    data_th = get_holiday_data(Lang.TH, year)
    data_en = get_holiday_data(Lang.EN, year)
    holiday = []
    for (data_key, entry) in data_en.items():
        date_stamp = f"{entry.year_ce}{entry.month_index+1:02d}{entry.day:02d}"
        holiday.append(Holiday(
            date_stamp = date_stamp,
            day_of_week_index = entry.day_of_week_index,
            day_of_week_th = entry.day_of_week_th,
            day_of_week_en = entry.day_of_week_en,
            day_of_week_abbr_en = entry.day_of_week_abbr_en,
            day_of_week_abbr_th = entry.day_of_week_abbr_th,
            day = entry.day,
            month_index = entry.month_index,
            month_th = entry.month_th,
            month_abbr_th = entry.month_abbr_th,
            month_en = entry.month_en,
            month_abbr_en = entry.month_abbr_en,
            year_ce = entry.year_ce,
            year_be = entry.year_be,
            description_th = data_th[data_key].description,
            description_en = entry.description
        )._asdict())

    return holiday


def get_holiday_data(lang: Lang, year: int) -> Dict[str, HolidayDetail]:
    url = get_holiday_url(lang, year)
    resp = get(url)
    holiday = {}
    if resp.status_code == 200:
        data = resp.json()
        if "holidayCalendarLists" in data:
            for entry in data["holidayCalendarLists"]:
                parsed_data = parse_date_entry(entry, lang)
                data_key = f"{parsed_data.year_ce}{parsed_data.month_index+1:02d}{parsed_data.day:02d}"
                holiday[data_key] = parsed_data

    return holiday


def parse_date_entry(holiday: BOTHoliday, lang: Lang) -> HolidayDetail:
    day_of_week, date = holiday["date"].split(" ")
    month_name = holiday["month"]
    year = holiday["year"]
    description = holiday["holidayDescription"].replace("\n", " ").replace("  ", " ").strip()
    day_of_week_index = get_day_of_week_index(day_of_week, lang)
    month_index = get_month_index(month_name, lang)
    day_of_month = int(date)
    year_be = int(year) if lang == Lang.TH else int(year) + 543
    year_ce = int(year) - 543 if lang == Lang.TH else int(year)
    day_of_week_name = get_day_of_week_name(day_of_week_index)
    month_name = get_month_name(month_index)

    return HolidayDetail(
            day_of_week_index = day_of_week_index,
            day_of_week_th = day_of_week_name["full_th"],
            day_of_week_en = day_of_week_name["full_en"],
            day_of_week_abbr_th = day_of_week_name["abbr_th"],
            day_of_week_abbr_en = day_of_week_name["abbr_en"],
            day = day_of_month,
            month_index = month_index,
            month_th = month_name["full_th"],
            month_abbr_th = month_name["abbr_th"],
            month_en = month_name["full_en"],
            month_abbr_en = month_name["abbr_en"],
            year_ce = year_ce,
            year_be = year_be,
            description = description
        )


def get_day_of_week_index(day_name: str, lang: Lang) -> int:
    day_names = {
        Lang.TH: [ "วันอาทิตย์", "วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์" ],
        Lang.EN: [ "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday" ]
    }

    return day_names[lang].index(day_name.lower())


def get_month_index(month_name: str, lang: Lang) -> int:
    month_names = {
        Lang.TH: [ "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม" ],
        Lang.EN: [ "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december" ]
    }

    return month_names[lang].index(month_name.lower())


def get_day_of_week_name(day_of_week_index: int) -> Dict[str, str]:
    day_of_week_names = {
        Lang.TH: {
            Name.FULL: ["วันอาทิตย์", "วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์"],
            Name.ABBR: ["อา.", "จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส."]
        },
        Lang.EN: {
            Name.FULL: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            Name.ABBR: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        }
    }

    return {
        "full_th": day_of_week_names[Lang.TH][Name.FULL][day_of_week_index],
        "abbr_th": day_of_week_names[Lang.TH][Name.ABBR][day_of_week_index],
        "full_en": day_of_week_names[Lang.EN][Name.FULL][day_of_week_index],
        "abbr_en": day_of_week_names[Lang.EN][Name.ABBR][day_of_week_index]
    }


def get_month_name(month_index: int) -> Dict[str, str]:
    month_names = {
        Lang.TH: {
            Name.FULL: [ "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"],
            Name.ABBR: [ "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
        },
        Lang.EN: {
            Name.FULL: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
            Name.ABBR: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        }
    }

    return {
        "full_th": month_names[Lang.TH][Name.FULL][month_index],
        "abbr_th": month_names[Lang.TH][Name.ABBR][month_index],
        "full_en": month_names[Lang.EN][Name.FULL][month_index],
        "abbr_en": month_names[Lang.EN][Name.ABBR][month_index]
    }


def create_hash(plain: str) -> str:
    md5_hash = hashlib.md5()
    md5_hash.update(plain.encode('utf-8'))  # Encode the string to bytes

    return md5_hash.hexdigest()


def is_data_change(new_hash: str) -> bool:
    try:
        with open(version_json_filename, 'r') as f:
            data = json.load(f)
        return data["hash"] != new_hash
    except FileNotFoundError:
        return True
    except json.JSONDecodeError:
        raise(f"Error: Invalid JSON")


def bump_version(new_hash: str, new_date: str):
    with open(readme_filename, 'r') as f:
        file_content = f.read()
    new_hash_content = f"<!--Version:Begin-->{new_hash}<!--Version:End-->"
    new_date_content = f"<!--Date:Begin-->{new_date}<!--Date:End-->"
    new_content = re.sub(r"<!--Version:Begin-->.+<!--Version:End-->", new_hash_content, file_content)
    new_content = re.sub(r"<!--Date:Begin-->.+<!--Date:End-->", new_date_content, new_content)
    with open(readme_filename, 'w') as f:
        f.write(new_content)


def dump_json_to_file(data: Any, file: IO[str]):
    json.dump(humps.camelize(data), file, indent=4, ensure_ascii=False)


def dump_json_to_string(data: Any) -> str:
    return json.dumps(humps.camelize(data), ensure_ascii=False)


if __name__ == "__main__":
    now = datetime.now()
    current_year = now.year
    next_year = current_year + 1
    current_year_holiday = HolidayInYear(
        year_be = current_year + 543,
        year_ce = current_year,
        data = get_holiday(current_year)
    )._asdict()
    next_year_holiday = HolidayInYear(
        year_be = next_year + 543,
        year_ce = next_year,
        data = get_holiday(next_year)
    )._asdict()
    holiday = [
        current_year_holiday,
        next_year_holiday
    ]
    holiday_json = dump_json_to_string(holiday)
    digest = create_hash(holiday_json)
    try:
        if is_data_change(digest):
            version_json = {
                "hash": digest
            }
            with open(version_json_filename, 'w') as f:
                dump_json_to_file(version_json, f)
            with open("data.json", "w") as f:
                dump_json_to_file(holiday, f)
            bump_version(digest, now.strftime("%b %d, %Y"))
            print("Date is updated.")
        else:
            print("Data is already up-to-date.")
    except Exception as e:
        print(e)
        sys.exit(1)