#%%
# where did the ESSER money go?
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import plotly.io as pio
from PIL import Image

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# plotly global stuff
custom_template = pio.templates["plotly_white"]
# custom_template.layout.font.family = "Castoro"
pio.templates.default = custom_template

# Step 2: Function to add "icon.png" to the bottom left-hand side of the figure
img = Image.open('icon.png')
def add_icon(fig, image_path="icon.png"):
    fig.add_layout_image(
        dict(
            source=img,
            xref="paper", yref="paper",
            x=0, y=0,
            sizex=0.15, sizey=0.15,
            xanchor="left", yanchor="bottom",
            opacity=1,
            layer="above"
        )
    )
    return fig

df_esser = pd.read_excel('./../data/raw/esser-federal-data.xlsx', sheet_name='prime') # data from https://covid-relief-data.ed.gov/data-download
df_enrollment = pd.read_excel('./../data/raw/enrollment.xlsx') # data from https://nces.ed.gov/programs/digest/d23/tables/dt23_203.20.asp

# merge, clean
state_abbreviation_to_name = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'DC': 'District of Columbia', 'FL': 'Florida',
    'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
    'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts',
    'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska',
    'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon',
    'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee',
    'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'PR': 'Puerto Rico'
}
df_esser['state_name'] = df_esser['stateCode'].map(state_abbreviation_to_name)
df_enrollment.columns = df_enrollment.columns.str.strip()
df_esser['state_name'] = df_esser['state_name'].str.strip()
df_enrollment['state'] = df_enrollment['state'].str.strip()
df = pd.merge(df_esser, df_enrollment, left_on='state_name', right_on='state')
df = df[df['stateCode'] != 'PR']

#impute
df['esserAllocated'] = df['esser1GrantAmountAllocated'] + df['esser2GrantAmountAllocated'] + df['esser3GrantAmountAllocated']

#impute from imputed
df['expenditure_per_student'] = df['esserAllocated'] / df['Fall 2019']

#%%
# Extract relevant columns
df_map = df[['stateCode', 'esserAllocated']]

# Clean the data (remove any $ symbols and commas from the grant amount and convert to numeric)
df_map['esserAllocated'] = df_map['esserAllocated'].replace({'\$': '', ',': ''}, regex=True).astype(float)

# Create the map
fig = px.choropleth(
    df_map,
    locations='stateCode',
    locationmode="USA-states",
    color='esserAllocated',
    color_continuous_scale="Viridis",
    scope="usa",
    labels={'esserAllocated':'ESSER I Grant Amount Allocated'},
    title="ESSER I Grant Amount Allocated by State"
)

fig = add_icon(fig, image_path="icon.png")

# Display the map
fig.show()
# %%
# Display the relevant columns to review
result_df = df[['stateCode', 'state_name', 'esser1GrantAmountAllocated', 'Fall 2019', 'expenditure_per_student']]

# Round the expenditure per student to two decimal places and add a dollar sign
result_df['expenditure_per_student'] = result_df['expenditure_per_student'].round(2)
result_df['expenditure_per_student'] = result_df['expenditure_per_student'].apply(lambda x: f"${x:,.2f}")

# Create a new column with numeric values for the continuous scale
result_df['expenditure_per_student_numeric'] = result_df['expenditure_per_student'].replace({'\$': '', ',': ''}, regex=True).astype(float)

# Calculate the rank of each state based on expenditure per student (1 for highest, 50 for lowest)
result_df['rank'] = result_df['expenditure_per_student_numeric'].rank(ascending=False).astype(int)

# Create the map using Plotly
fig = px.choropleth(
    result_df,
    locations='stateCode',  # Use state abbreviations for locations
    locationmode="USA-states",
    color='expenditure_per_student_numeric',  # Color by numeric expenditure per student for continuous scale
    color_continuous_scale="Viridis",  # Use a color scale (you can choose a different one if you prefer)
    scope="usa",  # Focus on the USA map
    labels={'expenditure_per_student_numeric': 'Expenditure per Student'},
    title="Expenditure per Student by State"
)

# Update the hover data to show the formatted expenditure per student and the rank
fig.update_traces(hovertemplate="<b>%{location}</b><br>Expenditure per Student: %{z:$,.2f}<br>Rank: %{customdata}/50",
                  customdata=result_df['rank'])

# Display the map
fig.show()
# %%

# Initialize the Dash app
app = dash.Dash(__name__)

# Dictionary mapping columns to natural language names
columns_with_names = {
    'anyEsserASeaDirectActivitiesLearningLoss': 'Did the state directly administer activities to address the learning loss of students disproportionately impacted by COVID-19?',
    'areEsser1SeaFundsAwarded': 'Did the state award ESSER I SEA Reserve Funds to local educational agencies (LEAs) during the reporting period?',
    'areEsser2SeaFundsAwarded': 'Did the state award ESSER II SEA Reserve Funds to LEAs during the reporting period?',
    'areEsser3LearningLossFundsAwarded': 'Did the state award ARP ESSER III Learning Loss Funds to LEAs during the reporting period?',
    'areEsser3SummerEnrichmentAwarded': 'Did the state award ARP ESSER III Summer Enrichment Funds to LEAs during the reporting period?',
    'areEsser3AfterschoolProgramsAwarded': 'Did the state award ARP ESSER III Afterschool Program Funds to LEAs during the reporting period?',
    'areEsser3OtherAwarded': 'Did the state award ARP ESSER III Other Reserve Funds to LEAs during the reporting period?',
    'areEsser1SeaNonLeaFundsAwarded': 'Did the state award ESSER I SEA Reserve Funds to non-LEA entities during the reporting period?',
    'areEsser2SeaNonLeaFundsAwarded': 'Did the state award ESSER II SEA Reserve Funds to non-LEA entities during the reporting period?',
    'areEsser3NonLeaLearningLossFundsAwarded': 'Did the state award ARP ESSER III Learning Loss Funds to non-LEA entities during the reporting period?',
    'areEsser3NonLeaSummerEnrichmentAwarded': 'Did the state award ARP ESSER III Summer Enrichment Funds to non-LEA entities during the reporting period?',
    'areEsser3NonLeaAfterschoolProgramsAwarded': 'Did the state award ARP ESSER III Afterschool Program Funds to non-LEA entities during the reporting period?',
    'areEsser3NonLeaOtherAwarded': 'Did the state award ARP ESSER III Other Reserve Funds to non-LEA entities during the reporting period?',
    'anyEsserAStrategiesIdentifyStudents': 'Did the state use any listed strategies to identify students disproportionately impacted by COVID-19?',
    'isEsserAIdentifiedByStudentDemographic': 'Did the state use demographic data to identify students disproportionately impacted by COVID-19?',
    'isEsserAIdentifiedByStudentOutcome': 'Did the state use student academic outcome data to identify students disproportionately impacted by COVID-19?',
    'isEsserAIdentifiedByOtherStudentOutcome': 'Did the state use other student outcome data to identify students disproportionately impacted by COVID-19?',
    'isEsserAIdentifiedByMissedDays': 'Did the state use data on missed in-person instruction days to identify students disproportionately impacted by COVID-19?',
    'isEsserAIdentifiedByOpportunityToLearn': 'Did the state use opportunity to learn data to identify students disproportionately impacted by COVID-19?',
    'isEsserAIdentifiedByStateAdministrativeData': 'Did the state use state administrative data to identify students disproportionately impacted by COVID-19?',
    'isEsserAIdentifiedByHealthData': 'Did the state use health data to identify students disproportionately impacted by COVID-19?',
    'isEsserAIdentifiedByStakeholderInput': 'Did the state use stakeholder input to identify students disproportionately impacted by COVID-19?',
    'isEsserAIdentifiedByOtherData': 'Did the state use other data to identify students disproportionately impacted by COVID-19?'
}


# Function to create choropleth map for each column
def create_choropleth(column):
    # Convert the boolean column to categorical strings for color mapping
    df[column] = df[column].map({True: 'True', False: 'False'})
    
    return px.choropleth(
        df,
        locations='stateCode',
        locationmode="USA-states",
        color=column,
        color_discrete_map={'True': 'teal', 'False': 'coral'},  # Consistent color scheme
        scope="usa",
        labels={column: "Legend"},  # Set the title for the legend
    )

# Layout with a dropdown and a graph
app.layout = html.Div([
    dcc.Dropdown(
        id='dropdown',
        options=[{'label': name, 'value': column} for column, name in columns_with_names.items()],
        value='anyEsserASeaDirectActivitiesLearningLoss',  # Default value
        clearable=False
    ),
    dcc.Graph(id='choropleth')
])

# Callback to update the graph based on dropdown selection
@app.callback(
    Output('choropleth', 'figure'),
    [Input('dropdown', 'value')]
)
def update_choropleth(selected_column):
    return create_choropleth(selected_column)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

# %%

# Initialize the Dash app
app = dash.Dash(__name__)

# List of columns related to data sources used to identify impacted students
data_source_columns = [
    'isEsserAIdentifiedByStudentDemographic',
    'isEsserAIdentifiedByStudentOutcome',
    'isEsserAIdentifiedByOtherStudentOutcome',
    'isEsserAIdentifiedByMissedDays',
    'isEsserAIdentifiedByOpportunityToLearn',
    'isEsserAIdentifiedByStateAdministrativeData',
    'isEsserAIdentifiedByHealthData',
    'isEsserAIdentifiedByStakeholderInput',
    'isEsserAIdentifiedByOtherData'
]

# Calculate the score for each state (number of data sources used)
df['data_source_score'] = df[data_source_columns].sum(axis=1)
df['data_source_score'] = df['data_source_score'].astype(float)

# Create the choropleth map with a continuous gradient color scale
fig = px.choropleth(
    df,
    locations='stateCode',
    locationmode="USA-states",
    color='data_source_score',
    color_continuous_scale='Viridis',  # Continuous gradient color scale
    scope="usa",
    labels={'data_source_score': 'Number of Data Sources Used'},
    title='Number of Data Sources Used to Identify Students Disproportionately Impacted by COVID-19'
)

# Show the figure
fig.show()
# %%
abbreviation_map = {
    'anyEsserASeaDirectActivitiesLearningLoss': 'Direct activities for learning loss',
    'areEsser1SeaFundsAwarded': 'ESSER I funds to LEAs',
    'areEsser2SeaFundsAwarded': 'ESSER II funds to LEAs',
    'areEsser3LearningLossFundsAwarded': 'ESSER III learning loss funds to LEAs',
    'areEsser3SummerEnrichmentAwarded': 'ESSER III summer enrichment to LEAs',
    'areEsser3AfterschoolProgramsAwarded': 'ESSER III afterschool programs to LEAs',
    'areEsser3OtherAwarded': 'ESSER III other funds to LEAs',
    'areEsser1SeaNonLeaFundsAwarded': 'ESSER I funds to non-LEAs',
    'areEsser2SeaNonLeaFundsAwarded': 'ESSER II funds to non-LEAs',
    'areEsser3NonLeaLearningLossFundsAwarded': 'ESSER III learning loss funds to non-LEAs',
    'areEsser3NonLeaSummerEnrichmentAwarded': 'ESSER III summer enrichment to non-LEAs',
    'areEsser3NonLeaAfterschoolProgramsAwarded': 'ESSER III afterschool programs to non-LEAs',
    'areEsser3NonLeaOtherAwarded': 'ESSER III other funds to non-LEAs',
    'anyEsserAStrategiesIdentifyStudents': 'Strategies to identify impacted students',
    'isEsserAIdentifiedByStudentDemographic': 'Demographic data',
    'isEsserAIdentifiedByStudentOutcome': 'Academic outcome data',
    'isEsserAIdentifiedByOtherStudentOutcome': 'Other student outcome data',
    'isEsserAIdentifiedByMissedDays': 'Missed days data',
    'isEsserAIdentifiedByOpportunityToLearn': 'Opportunity to learn data',
    'isEsserAIdentifiedByStateAdministrativeData': 'State administrative data',
    'isEsserAIdentifiedByHealthData': 'Health data',
    'isEsserAIdentifiedByStakeholderInput': 'Stakeholder input',
    'isEsserAIdentifiedByOtherData': 'Other data'
}

# Sum the counts for each data source and sort them
data_source_counts = df[data_source_columns].sum().sort_values(ascending=True)

# Map to natural language names using the abbreviation map
data_source_counts.index = data_source_counts.index.map(abbreviation_map)

# Create the bar chart
fig = px.bar(
    data_source_counts,
    x=data_source_counts.values,
    y=data_source_counts.index,
    orientation='h',
    labels={'x': 'Number of States', 'y': 'Data Source'},
    title="Usage of Data Sources to Identify Students Disproportionately Impacted by COVID-19"
)

# Update layout to address bar width and y-axis alignment
fig.update_layout(
    title_x=0.5,
    title_xanchor='center',
    height=600,  # Increase height to give bars more space
    yaxis=dict(
        automargin=True,  # Automatically manage margins to align the labels
        tickmode='linear'  # Ensure each label is aligned with its corresponding bar
    ),
    bargap=0.1  # Adjust gap between bars if needed
)

# Display the bar chart
fig.show()
# %%
