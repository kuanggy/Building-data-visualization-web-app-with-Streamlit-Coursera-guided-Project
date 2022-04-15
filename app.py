import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

data_url = 'https://data.cityofnewyork.us/api/views/h9gi-nx95/rows.csv?accessType=DOWNLOAD'

st.title('Motor Vehicle Collisions')
st.markdown('This application is made by Streamlit for learning purpose')

@st.cache(persist=True) #persist cache, so we don't reload the data everytime we rerun
def load_data(n_rows):
    df = pd.read_csv(data_url, nrows=n_rows, parse_dates=[['CRASH DATE', 'CRASH TIME']])
    df.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    lowercase = lambda x: str(x).lower()
    df.rename(lowercase, axis=1, inplace=True)
    df.rename(columns={
        'crash date_crash time':'date/time',
        'number of persons injured':'injured_persons',
        'number of pedestrians injured':'injured_pedestrians',
        'number of cyclist injured':'injured_cyclists',
        'number of motorist injured':'injured_motorists'
        }, inplace=True)
    return df

df = load_data(100000)
original_data = df

#show the map with latitude and longitude with slider
st.header('Where are the most people injured?')
injured_people = st.slider('Number of persons injured in Vehicle collisions', 0, 19,step=1)
st.map(df.query('injured_persons >= @injured_people')[['latitude', 'longitude']].dropna(how='any')) #we have performed .lower()

#Query: time and collisions using drop-down list
st.header('How many collisions occur during a given time of date?')
hour = st.slider('Hour to look at', 0,23,step=1)
st.markdown('Vehicle Collisions between %i:00 and %i:00' % (hour, (hour + 1) % 24))
df = df[df['date/time'].dt.hour == hour]

#making 3D visualization on the map
    #initialize the map
state_midpoint = (np.average(df['latitude']), np.average(df['longitude'])) #calculate mid point
st.write(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state={
        'latitude': state_midpoint[0]+0.2,
        'longitude': state_midpoint[1]-0.5,
        'zoom':11,
        'pitch': 50
    },
    #add layers of data you want to show
    layers=[
        pdk.Layer(
            'HexagonLayer',
            data=df[['date/time','latitude','longitude']],
            get_position=['longitude','latitude'], #because we moved from initial_view_state, then we want to get data from the moved coords
            radius=100, #meters
            extruded=True,
            pickable=True,
            elevation_scale=8,
            elevation_range=[0,1000],
        ),
    ],
))

#create charts and histogram
st.subheader('Breakdown by minute between %i:00 and %i:00'%(hour,(hour+1)%24))
filtered_data = df[
    (df['date/time'].dt.hour >= hour) & (df['date/time'].dt.hour < (hour+1))
]
hist = np.histogram(filtered_data['date/time'].dt.minute, bins=60, range=(0,60))[0]
    #create data frame
chart_data = pd.DataFrame({'minute':range(60), 'crashes': hist})
fig = px.bar(chart_data, x='minute',y='crashes', hover_data=['minute','crashes'], height=400)
st.write(fig)

#filter data, seeing ranking using dropdown
st.header('Top 5 dangerous street by affected type')
select = st.selectbox('Affected type of people', ['Pedestrians','Cyclists','Motorists'])
if select == "Pedestrians":
    st.write(original_data.query('injured_pedestrians >= 1')[['on street name', 'injured_pedestrians']].sort_values(by=['injured_pedestrians'], ascending=False).dropna(how='any').head(5))
elif select == "Cyclists":
    st.write(original_data.query('injured_cyclists >= 1')[['on street name', 'injured_cyclists']].sort_values(by=['injured_cyclists'], ascending=False).dropna(how='any').head(5))
else:
    st.write(original_data.query('injured_motorists >= 1')[['on street name', 'injured_motorists']].sort_values(by=['injured_motorists'], ascending=False).dropna(how='any').head(5))

#Create Check Box to show/not show the data table
if st.checkbox('Show Raw Data', False):
    st.subheader('Raw data of vehicle collisions')
    st.write(df)
    st.text(f'Number of queried data showed = {df.shape[0]}')