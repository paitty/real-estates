from playwright.sync_api import sync_playwright
import folium
import pandas as pd
import requests
import webbrowser
import random
import time
import json
import folium.plugins as plugins

# prints a random value from the list
list1 = [2, 3, 4]

headers = {'Accept':	'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding':	'gzip, deflate, br, zstd',
    'Accept-Language':	'en-US,fr;q=0.8,hr;q=0.5,en;q=0.3',
    'Connection':	'keep-alive',
    'DNT':	'1',
    'Host':	'nominatim.openstreetmap.org',
    'Priority':	'u=0, i',
    'Sec-Fetch-Dest':	'document',
    'Sec-Fetch-Mode':	'navigate',
    'Sec-Fetch-Site':	'none',
    'Sec-Fetch-User':	'?1',
    'Sec-GPC':	'1',
    'Upgrade-Insecure-Requests':	'1',
    'User-Agent':	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:135.0) Gecko/20100101 Firefox/135.0'}

def get_cities_from_Njuskalo():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.njuskalo.hr/prodaja-kuca/istra")
        page.click('button:has-text("Prihvati i zatvori")')
        page.click('button:has-text("RAZUMIJEM")')

        all_items = page.locator("li").all()
        list_of_cities=[]
        njuskalo_link=[]
        just_link=[]

        detail_list_of_cities=[]
        detail_njuskalo_link=[]
        detail_just_link=[]

        for item in all_items:
            if item.get_attribute("class")=='CategoryListing-topCategoryItem':
                item_element = item.locator("a")
                list_of_cities.append(item_element.inner_html().strip())
                just_link.append(item_element.get_attribute("href"))
                njuskalo_link.append('<a href=\''+item_element.get_attribute("href")+'\'>'+item_element.inner_html().strip()+'</a>')
        
        for link in just_link:
            time.sleep(1+random.choice(list1))
            page.goto(link)

            all_items = page.locator("li").all()

            for item in all_items:
                if item.get_attribute("class")=='CategoryListing-topCategoryItem':
                    item_element = item.locator("a")
                    detail_list_of_cities.append(item_element.inner_html().strip())
                    detail_just_link.append(item_element.get_attribute("href"))
                    detail_njuskalo_link.append('<a href=\''+item_element.get_attribute("href")+'\'>'+item_element.inner_html().strip()+'</a>')
                
        browser.close()

def save_cities_to_json(filename):
    lists = ['list_of_cities', 'njuskalo_link', 'just_link','detail_list_of_cities', 'detail_njuskalo_link', 'detail_just_link']

    data = {listname: globals()[listname] for listname in lists}
    with open(filename, 'w') as outfile:
        json.dump(data, outfile, indent=4)

def save_numbers_to_json(filename):
    lists = ['start_i','numbers_in_city']

    data = {listname: globals()[listname] for listname in lists}
    with open(filename, 'w') as outfile:
        json.dump(data, outfile, indent=4)

def open_from_json(output1_label, output2_label, filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    output1 = data[output1_label]
    output2  = data[output2_label]
    return output1, output2


def add_price_in_listings(link_list,max_price):
    output = []
    for link in link_list:
        output.append(link+'?price[max]='+str(max_price))
    return output

def display_cities_on_map(list_of_cities, just_link, numbers_in_city, html_filename):

    #headers={'User-Agent': 'Mozilla/5.0'}

    latitudes = []
    longitudes = []
    for i in range(len(numbers_in_city)):
        if numbers_in_city[i] == '0':
            numbers_in_city[i]='-'
    for city in list_of_cities:            
            if city == 'Monteserpo - Komunal':
                city = 'MONTE sERPO'
            city=city + ', istra'
            print(city)
            url='https://nominatim.openstreetmap.org/search.php?q='+city+'&format=jsonv2'
            r= requests.get(url, headers=headers)
            if r.json() == []:
                url='https://nominatim.openstreetmap.org/search.php?q='+city.split()[0]+'&format=jsonv2'
                r= requests.get(url, headers=headers)
            latitudes.append(r.json()[0]['lat'])
            longitudes.append(r.json()[0]['lon'])
            
    njuskalo_link = just_link
    for i in range(len(just_link)):
        njuskalo_link[i] = '<a href="'+just_link[i]+'" target=”_blank”>'+list_of_cities[i]+'</a>'
    
    df = pd.DataFrame({'Properties':njuskalo_link,
                        'Numbers':numbers_in_city, 
                        'Latitude':latitudes,
                        'Longitude':longitudes})

    m = folium.Map(location=[45.1816824,13.86411], tiles="OpenStreetMap", zoom_start=10)

    for i in range(0,len(df)):
        point_location=[df.iloc[i]['Latitude'], df.iloc[i]['Longitude']]
        duration = get_duration(point_location)
        if duration < 20:
            icon_color ="#004506" #green
        elif duration <30:
            icon_color = "#2efa00" #light green
        elif duration < 45:
            icon_color = "#bcd100" #yellow
        else:
            icon_color = "#e62c0b" #red
        print(df.iloc[i]['Properties'])
        folium.Marker(
        location=point_location,
        icon=plugins.BeautifyIcon(icon="arrow-down", icon_shape="marker",number=df.iloc[i]['Numbers'], border_color=icon_color, text_color=icon_color),
        popup=df.iloc[i]['Properties'],
        ).add_to(m)
    m = add_categorical_legend(m, 'Distance to Rovinj:',
                             colors = ['#004506',"#2efa00","#bcd100", "#e62c0b"],
                           labels = ['< 20 min', '< 30 min', '< 45 min', '>= 45min'])
    m.save(html_filename)
    webbrowser.get('firefox').open_new_tab('file:////Users/pierre-adrien.itty/Downloads/scraper/'+html_filename)

def get_numbers_from_njuskalo(just_link):
    numbers_in_city = []
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.njuskalo.hr/prodaja-kuca/istra")
        page.click('button:has-text("Prihvati i zatvori")')
        page.click('button:has-text("RAZUMIJEM")')
        for link in just_link:
            number = 0
            time.sleep(random.choice(list1))
            page.goto(link)
            page.mouse.wheel(0, 1500)
            all_items = page.locator("strong").all()
            for item in all_items:
                if item.get_attribute("class")=='entities-count':
                    number = item.inner_html().strip()
            numbers_in_city.append(number)   
        browser.close()
    return numbers_in_city

def add_categorical_legend(folium_map, title, colors, labels):
    if len(colors) != len(labels):
        raise ValueError("colors and labels must have the same length.")

    color_by_label = dict(zip(labels, colors))
    
    legend_categories = ""     
    for label, color in color_by_label.items():
        legend_categories += f"<li><span style='background:{color}'></span>{label}</li>"
        
    legend_html = f"""
    <div id='maplegend' class='maplegend'>
      <div class='legend-title'>{title}</div>
      <div class='legend-scale'>
        <ul class='legend-labels'>
        {legend_categories}
        </ul>
      </div>
    </div>
    """
    script = f"""
        <script type="text/javascript">
        var oneTimeExecution = (function() {{
                    var executed = false;
                    return function() {{
                        if (!executed) {{
                             var checkExist = setInterval(function() {{
                                       if ((document.getElementsByClassName('leaflet-top leaflet-right').length) || (!executed)) {{
                                          document.getElementsByClassName('leaflet-top leaflet-right')[0].style.display = "flex"
                                          document.getElementsByClassName('leaflet-top leaflet-right')[0].style.flexDirection = "column"
                                          document.getElementsByClassName('leaflet-top leaflet-right')[0].innerHTML += `{legend_html}`;
                                          clearInterval(checkExist);
                                          executed = true;
                                       }}
                                    }}, 100);
                        }}
                    }};
                }})();
        oneTimeExecution()
        </script>
      """
   

    css = """

    <style type='text/css'>
      .maplegend {
        z-index:9999;
        float:right;
        background-color: rgba(255, 255, 255, 1);
        border-radius: 5px;
        border: 2px solid #bbb;
        padding: 10px;
        font-size:12px;
        positon: relative;
      }
      .maplegend .legend-title {
        text-align: left;
        margin-bottom: 5px;
        font-weight: bold;
        font-size: 90%;
        }
      .maplegend .legend-scale ul {
        margin: 0;
        margin-bottom: 5px;
        padding: 0;
        float: left;
        list-style: none;
        }
      .maplegend .legend-scale ul li {
        font-size: 80%;
        list-style: none;
        margin-left: 0;
        line-height: 18px;
        margin-bottom: 2px;
        }
      .maplegend ul.legend-labels li span {
        display: block;
        float: left;
        height: 16px;
        width: 30px;
        margin-right: 5px;
        margin-left: 0;
        border: 0px solid #ccc;
        }
      .maplegend .legend-source {
        font-size: 80%;
        color: #777;
        clear: both;
        }
      .maplegend a {
        color: #777;
        }
    </style>
    """

    folium_map.get_root().header.add_child(folium.Element(script + css))

    return folium_map

def get_duration(location):
    rovinj = "13.640872,45.082166"
    destination = location[1]+","+location[0]
    url = "http://router.project-osrm.org/table/v1/driving/"+rovinj+";"+destination
    r= requests.get(url)
    duration = r.json()['durations'][0][1]/60
    return duration


list_of_cities, just_link = open_from_json('detail_list_of_cities','detail_just_link','city_save.json')

just_link = add_price_in_listings(just_link,200000)


numbers_in_city = [''] * len(just_link)
start_i=0

#start_i, numbers_in_city = open_from_json('start_i','numbers_in_city','numbers_save_2.json')

#while len(just_link) > start_i:
#    start = start_i
#    end =min(len(just_link),start_i+10)
#    numbers_in_city[start:end] = get_numbers_from_njuskalo(just_link[start:end])
#    start_i=min(len(just_link),start_i+10)
#    save_numbers_to_json('numbers_save_2.json')



start_i, numbers_in_city = open_from_json('start_i','numbers_in_city','numbers_save.json')

#list_of_cities = list_of_cities[:6]
#just_link = just_link[:6]
#numbers_in_city = numbers_in_city[:6]
#numbers_in_city = get_numbers_from_njuskalo(just_link)
#numbers_in_city = ['13', '75', '26', '38', '95', '52', '5', '0', '22', '13', '43', '12', '5', '33', '82', '29', '49', '44', '142', '26', '44', '8', '49', '14', '25', '55', '111', '37', '3', '30', '5', '13', '8', '53', '3', '21', '20', '42', '5', '124', '8', '26']
#numbers_in_city =  ['13', '0', '0', '1', '47', '0', '0', '3', '0', '3', '1', '0', '0', '1', '2', '1', '0', '5', '0', '4', '0', '2', '2', '0', '0', '3', '24', '0', '2', '1', '0', '0', '22', '0', '0', '2', '2', '2', '1', '1', '0', '5', '0', '1', '1', '1', '46', '0', '0', '0', '8', '5', '0', '1', '1', '0', '1', '1', '2', ...]
pass
#numbers_in_city = [''] * len(just_link)

display_cities_on_map(list_of_cities, just_link, numbers_in_city, 'detail_footprint.html')