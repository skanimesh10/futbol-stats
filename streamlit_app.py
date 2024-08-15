import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

LEAGUES = [
    {"name": "Premier League", "id": "9"},
    {"name": "La Liga", "id": "12"},
    {"name": "Bundesliga", "id": "20"},
    {"name": "Serie A", "id": "11"},
    {"name": "Ligue 1", "id": "13"}
]

@st.cache_data(ttl=3600)
def scrape_and_process_data(season, league_name, league_id, data_type):
    year1, year2 = season.split('-')
    
    if data_type == "Standings":
        url = f"https://fbref.com/en/comps/{league_id}/{year1}-{year2}/{year1}-{year2}-{league_name.replace(' ', '-')}-Stats"
    else:  # Fixtures
        url = f"https://fbref.com/en/comps/{league_id}/{year1}-{year2}/schedule/{year1}-{year2}-{league_name.replace(' ', '-')}-Scores-and-Fixtures"

    try:
        tables = pd.read_html(url)
        if tables:
            df = tables[0]

            # Clean up column names
            df.columns = df.columns.get_level_values(-1)
            df.columns = df.columns.str.strip()

            if data_type == "Standings":
                columns_to_keep = {
                    'Rk': 'Rank',
                    'Squad': 'Team',
                    'MP': 'Matches Played',
                    'W': 'Wins',
                    'D': 'Draws',
                    'L': 'Losses',
                    'GF': 'Goals For',
                    'GA': 'Goals Against',
                    'GD': 'Goal Difference',
                    'Pts': 'Points',
                    'Attendance': 'Attendance'
                }
            else:  # Fixtures
                columns_to_keep = {
                    'Date': 'Date',
                    'Time': 'Time',
                    'Home': 'Home Team',
                    'Score': 'Score',
                    'Away': 'Away Team',
                    'Attendance': 'Attendance',
                    'Venue': 'Venue'
                }

            df_selected = df[columns_to_keep.keys()].rename(columns=columns_to_keep)

            return df_selected
        else:
            st.error(f"No tables found for the {season} season.")
            return None
    except Exception as e:
        st.error(f"Error scraping data: {str(e)}")
        return None

def create_bar_chart(df):
    # Create a bar chart of points by team
    bar_fig = px.bar(df, x='Team', y='Points', title='Team Points')
    bar_fig.update_layout(xaxis_tickangle=-45)
    return bar_fig

def create_circular_comparison(df):
    # Automatically select the top two teams based on rank
    top_two_teams = df.nsmallest(2, 'Rank')['Team'].tolist()
    default_team1, default_team2 = top_two_teams

    Allow user to select teams for comparison with the top two as default
    team1 = st.selectbox("Select first team", df['Team'].unique(), index=df['Team'].tolist().index(default_team1))
    team2 = st.selectbox("Select second team", df['Team'].unique(), index=df['Team'].tolist().index(default_team2))


    # Get data for selected teams
    team1_data = df[df['Team'] == team1].iloc[0]
    team2_data = df[df['Team'] == team2].iloc[0]

    # Create circular chart
    categories = ['Matches Played', 'Wins', 'Draws', 'Losses', 'Goals For', 'Goals Against', 'Points']
    circle_fig = go.Figure()

    circle_fig.add_trace(go.Scatterpolar(
        r=[team1_data[cat] for cat in categories],
        theta=categories,
        fill='toself',
        name=team1,
        line_color='blue'
    ))
    circle_fig.add_trace(go.Scatterpolar(
        r=[team2_data[cat] for cat in categories],
        theta=categories,
        fill='toself',
        name=team2,
        line_color='lightblue'
    ))

    circle_fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(df[categories].max())]
            )),
        showlegend=True,
        title=f"Comparison between {team1} and {team2}"
    )

    return circle_fig


def fetch_and_display_data(season, league, league_id, data_type):
    with st.spinner("Fetching data..."):
        df = scrape_and_process_data(season, league, league_id, data_type)

    if df is not None:
        st.success("Data fetched successfully!")

        # Display data
        st.header(f"{league} {data_type} - Season {season}")
        st.dataframe(df)

        # Display visualizations
        if data_type == "Standings":
            st.subheader("Points Visualization")
            bar_fig = create_bar_chart(df)
            st.plotly_chart(bar_fig)
            
            st.subheader("Team Comparison")
            circle_fig = create_circular_comparison(df)
            st.plotly_chart(circle_fig)
        else:
            # Add fixture visualization here if needed
            pass
    else:
        st.error("Failed to fetch data. Please try again.")

def main():
    st.title("Football League Data Dashboard")

    # Sidebar for user input
    st.sidebar.title("Filters")

    # League selection
    selected_league = st.sidebar.selectbox("Select League", [league["name"] for league in LEAGUES])
    league_id = next(league["id"] for league in LEAGUES if league["name"] == selected_league)

    # Generate season options (assuming data available from 2010-2011 to 2023-2024)
    seasons = [f"{year}-{year + 1}" for year in range(2010, 2024)]
    selected_season = st.sidebar.selectbox("Select Season", seasons[::-1])  # Reverse order to show latest first

    # Add dropdown for selecting between standings and fixtures
    data_type = st.sidebar.selectbox("Select Data Type", ["Standings", "Fixtures"])

    # Fetch and display data based on selection
    fetch_and_display_data(selected_season, selected_league, league_id, data_type)

    # Add a note about data source
    st.sidebar.markdown("---")
    st.sidebar.info("Data sourced from fbref.com")

if __name__ == "__main__":
    main()
