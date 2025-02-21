import requests
from bs4 import BeautifulSoup
import json
import argparse

def get_course_info(date):
    url = f"https://www.equidia.fr/courses-hippique?date={date}"
    headers = {"User-Agent": "Mozilla/5.0"}  # Éviter le blocage par certains sites
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("Erreur lors de la récupération de la page.")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    courses = []
    race_divs = soup.find_all("div", class_="row clickable table-row row-reunion fill-primary-blue-50 text-primary-blue-50 finish-row")
    
    for race in race_divs:
        if race.find("use", {"xlink:href": "#discipline-galop"}):
            reunion_tag = race.find("use")["xlink:href"].replace("#logo-", "").strip()
            course_count_text = race.find("div", class_="block-course-discipline").find("span").text.strip()
            nombre_courses = course_count_text.split(" ")[0] if course_count_text else "0"
            
            courses.append({
                "date": date,
                "reunion": reunion_tag,
                "nombre_courses": nombre_courses
            })
    
    return courses

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="Date des courses au format AAAA-MM-JJ")
    args = parser.parse_args()
    
    results = get_course_info(args.date)
    
    with open("list_course.json", "w") as json_file:
        json.dump(results, json_file, indent=4)