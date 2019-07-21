import pandas as pd
import requests
def road_keeper_street_extraction_util(file_path, maps_key, latlng_column, rows_to_extract)
    data=pd.read_excel(file_path)
    data_filtered=data[~(data['נ״צ מדווח'].astype('str')=='0.0,0.0')]
    data_filtered.dropna(subset=['נ״צ מדווח'], inplace=True)
    data_filtered=data_filtered.iloc[:rows_to_extract]
    data_filtered['עיר']=''
    data_filtered['רחוב']=''
    data_filtered['מספר רחוב']=''
    data_filtered['כביש']=''
    data_filtered['צומת']=''
    data_filtered['כתובת']=''
    results=[]
    for i in range(rows_to_extract):
        result=requests.get('https://maps.googleapis.com/maps/api/geocode/json?latlng={0}&key={1}&language=iw&region=IL'.format(data_filtered.iloc[i]['נ״צ מדווח'],maps_key))
        street_number=''
        street=''
        road=''
        intersection=''
        city=''
        address=''
        for item in result.json()['results'][0]['address_components']:
            if 'street_number' in item['types']:
                street_number=item['short_name']
            elif 'route' in item['types']:
                if street_number!='':
                    street=item['long_name']
                else:
                    road=item['short_name']
            elif 'locality' in item['types']:
                city=item['long_name']
            elif 'administrative_area_level_2' in item['types'] and city=='':
                city=item['long_name']
            elif 'establishment' in item['types'] or 'intersection' in item['types']:
                intersection=item['long_name']
        address=result.json()['results'][0]['formatted_address']
        data_filtered.loc[i, 'עיר']=city
        data_filtered.loc[i, 'רחוב']=street
        data_filtered.loc[i, 'מספר רחוב']=street_number
        data_filtered.loc[i, 'כביש']=road
        data_filtered.loc[i, 'צומת']=intersection
        data_filtered.loc[i, 'כתובת']=address
    file_name='.'.join(file_path.split('.')[:-1])
    data_filtered.to_excel(file_name+'_post_extraction.xlsx')