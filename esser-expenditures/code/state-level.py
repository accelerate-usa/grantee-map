#%%
# where did the ESSER money go?
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import plotly.io as pio
from PIL import Image
import plotly.offline as offline
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import norm, shapiro
import plotly.graph_objects as go

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# plotly global stuff
custom_template = pio.templates["plotly_white"]
# custom_template.layout.font.family = "Castoro"
pio.templates.default = custom_template

# Step 2: Function to add "icon.png" to the bottom left-hand side of the figure
img = Image.open('icon.png')
def add_icon(fig):
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

df['esser1expendpercent'] = 1 - (df['esser1GrantAmountRemaining'] / df['esser1GrantAmountAllocated'])
df['esser2expendpercent'] = 1 - (df['esser2GrantAmountRemaining'] / df['esser2GrantAmountAllocated'])
df['esser3expendpercent'] = 1 - (df['esser3GrantAmountRemaining'] / df['esser3GrantAmountAllocated'])

df['totalAmountRemaining'] = df['esser1GrantAmountRemaining'] + df['esser2GrantAmountRemaining'] + df['esser3GrantAmountRemaining']
df['totalAmountAllocated'] = df['esser1GrantAmountAllocated'] + df['esser2GrantAmountAllocated'] + df['esser3GrantAmountAllocated']

#impute from imputed
df['expenditure_per_student'] = df['esserAllocated'] / df['Fall 2019']
df['totalesserspent'] = 1 - (df['totalAmountRemaining'] / df['totalAmountAllocated'])

# %%
# how much spent per state
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
    title="How much ESSER funding was allocated to each state?"
)

fig.update_traces(
    showscale=False  # Hide the color scale (legend)
)

fig.update_layout(
    title={
        'text':'How much ESSER funding was allocated to each state?',
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': dict(size=40, family="Castoro", color="black")
    },
)

# Display the map
offline.plot(fig, filename='./../figures/state-esser-allocations.html', auto_open=False)
fig.show()

#%%
# histogram

stat, p_value = shapiro(df['esserAllocated'])

hover_data = {
    'stateCode': True,  # Show the stateCode
    'esserAllocated': ':.2f'  # Show the esserAllocated with 2 decimal places
}

# Create the Plotly histogram
fig = px.histogram(
    df,
    x='esserAllocated',
    nbins=30,  # Adjust the number of bins
    color='stateCode',  # Use stateCode to differentiate states in hover
    hover_data=hover_data,
    labels={'esserAllocated': 'ESSER Allocated'},
    title='Histogram of ESSER Allocated',
    color_discrete_map={state: 'rgb(0, 51, 102)' for state in df['stateCode'].unique()}
)

# Update layout for a modern look and remove the legend
fig.update_layout(
    xaxis_title='ESSER Allocated',
    yaxis_title='Frequency',
    title_font=dict(size=20, family='Arial', color='darkblue'),
    xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGrey'),
    yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGrey'),
    plot_bgcolor='whitesmoke',
    bargap=0.1,
    showlegend=False  # Remove the legend
)

# line 
# Calculate the mean and standard deviation for the normal distribution curve
mean = np.mean(df['esserAllocated'])
std_dev = np.std(df['esserAllocated'])

# Generate x values for the normal distribution curve
x_values = np.linspace(min(df['esserAllocated']), max(df['esserAllocated']), 100)
y_values = norm.pdf(x_values, mean, std_dev) * len(df) * (max(df['esserAllocated']) - min(df['esserAllocated'])) / 30  # Scale the y values to match the histogram

# Add the normal distribution curve to the plot
fig.add_trace(go.Scatter(x=x_values, y=y_values, mode='lines', name='Normal Distribution', line=dict(color='darkblue', width=2)))

note_text = f'Shapiro-Wilk Test: Statistic={stat:.4f}, p-value={p_value:.4f}'
fig.add_annotation(
    text=note_text,
    xref='paper', yref='paper',
    x=0, y=-0.15,
    showarrow=False,
    font=dict(size=12, color="darkblue")
)

# Show the figure
offline.plot(fig, filename='./../figures/state-esser-allocations-histogram.html', auto_open=False)
fig.show()

#%%
# how much spent per student
result_df = df

result_df['expenditure_per_student_numeric'] = pd.to_numeric(result_df['expenditure_per_student'].replace({'\$': '', ',': ''}, regex=True), errors='coerce')
result_df['expenditure_per_student'] = result_df['expenditure_per_student_numeric'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
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
fig.update_traces(hovertemplate="<b>%{location}</b><br>Expenditure per Student: %{z:$,.2f}<br>Rank: %{customdata}/51",
                  customdata=result_df['rank'])

fig.update_layout(
    title={
        'text':'How much ESSER funding was allocated per student?',
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': dict(size=40, family="Castoro", color="black")
    },
)

# Display the map
offline.plot(fig, filename='./../figures/state-esser-allocations-per-student.html', auto_open=False)
fig.show()

# %%
# histogram

df['expenditure_per_student_numeric'] = pd.to_numeric(df['expenditure_per_student'].replace({'\$': '', ',': ''}, regex=True), errors='coerce')

# Perform the Shapiro-Wilk test on the numeric data
stat, p_value = shapiro(df['expenditure_per_student_numeric'].dropna())

hover_data = {
    'stateCode': True,  # Show the stateCode
    'expenditure_per_student_numeric': ':.2f'  # Show the expenditure with 2 decimal places
}

# histogram plot
num_states = len(df['stateCode'].unique())

# Generate a color scale with enough shades of blue for all states
blues = plotly.colors.sample_colorscale('Blues', [0.2 + n / num_states * 0.8 for n in range(num_states)])

# Create the color_discrete_map with different shades of blue for each state
color_discrete_map = {state: blues[i] for i, state in enumerate(df['stateCode'].unique())}

# Create the Plotly histogram
fig = px.histogram(
    df,
    x='expenditure_per_student_numeric',
    nbins=30,  # Adjust the number of bins
    color='stateCode',  # Use stateCode to differentiate states in hover
    hover_data=hover_data,
    labels={'expenditure_per_student_numeric': 'Expenditure per Student'},
    title='Histogram of Expenditure per Student',
    color_discrete_map=color_discrete_map  # Apply varying blue shades
)

# Update layout for a modern look and remove the legend
fig.update_layout(
    xaxis_title='Expenditure per Student',
    yaxis_title='Frequency',
    title_font=dict(size=20, family='Arial', color='darkblue'),
    xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGrey'),
    yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGrey'),
    plot_bgcolor='whitesmoke',
    bargap=0.1,
    showlegend=False  # Remove the legend
)

# Calculate the mean and standard deviation for the normal distribution curve
mean = np.mean(df['expenditure_per_student_numeric'])
std_dev = np.std(df['expenditure_per_student_numeric'])

# Generate x values for the normal distribution curve
x_values = np.linspace(min(df['expenditure_per_student_numeric']), max(df['expenditure_per_student_numeric']), 100)
y_values = norm.pdf(x_values, mean, std_dev) * len(df) * (max(df['expenditure_per_student_numeric']) - min(df['expenditure_per_student_numeric'])) / 30  # Scale the y values to match the histogram

# Add the normal distribution curve to the plot
fig.add_trace(go.Scatter(x=x_values, y=y_values, mode='lines', name='Normal Distribution', line=dict(color='darkblue', width=2)))

note_text = f'Shapiro-Wilk Test: Statistic={stat:.4f}, p-value={p_value:.4f}'
fig.add_annotation(
    text=note_text,
    xref='paper', yref='paper',
    x=0, y=-0.15,
    showarrow=False,
    font=dict(size=12, color="darkblue")
)

# Show the figure
offline.plot(fig, filename='./../figures/state-esser-allocations-histogram.html', auto_open=False)
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
#     'anyEsserAStrategiesIdentifyStudents': 'Did the state use any listed strategies to identify students disproportionately impacted by COVID-19?',
#     'isEsserAIdentifiedByStudentDemographic': 'Did the state use demographic data to identify students disproportionately impacted by COVID-19?',
#     'isEsserAIdentifiedByStudentOutcome': 'Did the state use student academic outcome data to identify students disproportionately impacted by COVID-19?',
#     'isEsserAIdentifiedByOtherStudentOutcome': 'Did the state use other student outcome data to identify students disproportionately impacted by COVID-19?',
#     'isEsserAIdentifiedByMissedDays': 'Did the state use data on missed in-person instruction days to identify students disproportionately impacted by COVID-19?',
#     'isEsserAIdentifiedByOpportunityToLearn': 'Did the state use opportunity to learn data to identify students disproportionately impacted by COVID-19?',
#     'isEsserAIdentifiedByStateAdministrativeData': 'Did the state use state administrative data to identify students disproportionately impacted by COVID-19?',
#     'isEsserAIdentifiedByHealthData': 'Did the state use health data to identify students disproportionately impacted by COVID-19?',
#     'isEsserAIdentifiedByStakeholderInput': 'Did the state use stakeholder input to identify students disproportionately impacted by COVID-19?',
#     'isEsserAIdentifiedByOtherData': 'Did the state use other data to identify students disproportionately impacted by COVID-19?'
}


# Function to create choropleth map for each column
def create_choropleth(column):
    # Create a copy of the DataFrame to avoid modifying it in place
    df_copy = df.copy()
    # Map the boolean column to strings in the copied DataFrame
    df_copy[column] = df_copy[column].map({True: 'True', False: 'False'})
    
    return px.choropleth(
        df_copy,
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
#%%

import plotly.graph_objects as go
import pandas as pd

# Assuming df is your DataFrame with necessary data
# Ensure df has 'stateCode' and the boolean columns in 'columns_with_names'

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
}

# Create a copy of the DataFrame to avoid modifying it in place
df_copy = df.copy()

# Map boolean columns to numerical values for z, and 'Yes'/'No' for text
for column in columns_with_names.keys():
    df_copy[column + '_num'] = df_copy[column].map({True: 1, False: 0})
    df_copy[column + '_text'] = df_copy[column].map({True: 'Yes', False: 'No'})

# Initialize the figure
fig = go.Figure()

# Define the colorscale mapping 0 to 'coral' and 1 to 'teal'
colorscale = [
    [0.0, '#304A6F'],
    [0.4999, '#304A6F'],
    [0.5, '#10A59C'],
    [1.0, '#10A59C']
]

# Add a choropleth trace for each column
for i, (column, name) in enumerate(columns_with_names.items()):
    fig.add_trace(go.Choropleth(
        locations=df_copy['stateCode'],
        z=df_copy[column + '_num'],
        text=df_copy[column + '_text'],  # Use 'Yes'/'No' for hover text
        locationmode="USA-states",
        colorscale=colorscale,
        zmin=0,
        zmax=1,
        marker_line_color='white',
        colorbar=dict(
            title="",
            tickvals=[0, 1],
            ticktext=['No', 'Yes'],
        ),
        hovertemplate='<b>%{location}</b><br>%{text}<extra></extra>',
        visible=(i == 0),  # Only the first trace is visible initially
        showscale=True  # Remove the legend
    ))

# Create the dropdown menu buttons
buttons = []
for i, (column, name) in enumerate(columns_with_names.items()):
    # Hide all traces initially
    visible = [False] * len(columns_with_names)
    # Make the selected trace visible
    visible[i] = True
    button = dict(
        label=name,
        method='update',
        args=[
            {'visible': visible},
            {'title': ''}  # Remove the title
        ]
    )
    buttons.append(button)

# Update the figure layout with dropdown menu and set the font to Poppins
fig.update_layout(
    updatemenus=[dict(
        buttons=buttons,
        direction='down',
        pad={'r': 10, 't': 10},
        showactive=True,
        x=0.5,
        xanchor='center',
        y=1.0,
        yanchor='top',
        font=dict(family='Poppins', size=16),
    )],
    margin=dict(l=0, r=0, t=50, b=0),
    geo=dict(scope='usa'),
)

# Display the figure
fig.write_html("./../figures/state_esser_uses.html")
fig.show()


# %%

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

# Mapping for natural language abbreviations
data_source_mapping = {
    'isEsserAIdentifiedByStudentDemographic': 'Student Demographic',
    'isEsserAIdentifiedByStudentOutcome': 'Student Outcome',
    'isEsserAIdentifiedByOtherStudentOutcome': 'Other Student Outcome',
    'isEsserAIdentifiedByMissedDays': 'Missed Days',
    'isEsserAIdentifiedByOpportunityToLearn': 'Opportunity to Learn',
    'isEsserAIdentifiedByStateAdministrativeData': 'State Administrative Data',
    'isEsserAIdentifiedByHealthData': 'Health Data',
    'isEsserAIdentifiedByStakeholderInput': 'Stakeholder Input',
    'isEsserAIdentifiedByOtherData': 'Other Data'
}

# Calculate the score for each state (number of data sources used)
df['data_source_score'] = df[data_source_columns].sum(axis=1)
df['data_source_score'] = df['data_source_score'].astype(float)

# Create a hover data column that lists the data sources used
def get_data_sources_used(row):
    used_sources = [data_source_mapping[col] for col in data_source_columns if row[col] == 1]
    return ', '.join(used_sources)

df['data_sources_used'] = df.apply(get_data_sources_used, axis=1)

# Create the choropleth map with a continuous gradient color scale
fig = px.choropleth(
    df,
    locations='stateCode',
    locationmode="USA-states",
    color='data_source_score',
    color_continuous_scale='Viridis',  # Continuous gradient color scale
    scope="usa",
    labels={'data_source_score': 'Number of Data Sources Used'},
    title='What data is used to identify students hit hardest by COVID-19?',
    hover_data={
        'stateCode': False,              # State code is not shown here; it's shown in the hovertemplate
        'data_source_score': True,       # Number of data sources used
        'data_sources_used': True        # List of data sources used
    }  
)

fig.update_layout(
    title={
        'text':'What data is used to identify students hit hardest by COVID-19?',
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': dict(size=40, family="Castoro", color="black")
    },
)

# Make sure to pass `customdata` to the trace to use in hovertemplate
fig.update_traces(
    customdata=df[['data_sources_used']],  # Pass the custom data to the trace
    hovertemplate="<b>%{location}</b><br>" +   # State name (uses location value)
                  "Number of Data Sources Used: %{z}<br>" +  # Show the number of data sources
                  "Sources: %{customdata[0]}"  # Correctly reference custom data for sources
)

fig.show()
# Output to HTML
fig.write_html("./../figures/state_data_used.html")
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

# Create a dictionary to store states that used each data source
data_source_states = {}

for col in data_source_columns:
    data_source_name = abbreviation_map[col]
    # List of states that used this data source
    states_using_source = df.loc[df[col] == 1, 'stateCode'].tolist()
    # Join list of states into a single string
    data_source_states[data_source_name] = ', '.join(states_using_source)

# Prepare custom hover data
custom_hover_data = [[data_source_states[data_source]] for data_source in data_source_counts.index]

# Create the bar chart
fig = px.bar(
    data_source_counts,
    x=data_source_counts.values,
    y=data_source_counts.index,
    orientation='h',
    labels={'x': 'Number of States', 'y': 'Data Source'},
    title="Distribution of data sources used to identify students hit hardest by COVID-19"
)

# Update hover template to include states
fig.update_traces(
    customdata=custom_hover_data,  # Attach the custom hover data
    hovertemplate="<b>%{y}</b><br>" +  # Data source name
                  "Number of States: %{x}<br>" +  # Number of states
                  "States: %{customdata[0]}",  # States that used the data source
    marker=dict(color='#304A6F')
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

fig.update_layout(
    font=dict(
        family="Poppins",
        size=16,  # Default font size
        color="black"  # Default font color
    ),
    title={
        'text': "Distribution of data sources used to identify students hit hardest by COVID-19",
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': dict(size=40, family="Castoro", color="black")  # Override title font
    },
    height=600,  # Increase height to give bars more space
    bargap=0.1  # Adjust gap between bars if needed
)

# Display the bar chart
fig.write_html("./../figures/state_data_used_bar.html")
fig.show()

# %%
# What percent of ESSER funds are spent?

columns = [
    ('totalesserspent', 'What Percent of ESSER Funds are Spent?    '),
    ('esser1expendpercent', 'What Percent of ESSER I is Spent?    '),
    ('esser2expendpercent', 'What Percent of ESSER II is Spent?    '),
    ('esser3expendpercent', 'What Percent of ESSER III is Spent?    '),

]

# Initialize the figure
fig = go.Figure()

# Add a choropleth trace for each ESSER fund
for i, (col, title) in enumerate(columns):
    fig.add_trace(go.Choropleth(
        locations=df['stateCode'],
        z=df[col],
        locationmode='USA-states',
        colorscale="Viridis",
        colorbar=dict(
            title="Percentage Spent",
            tickformat=".0%"
        ),
        zmin=0,
        zmax=1,
        visible=(i == 0),  # Only the first trace is visible initially
        name=title,
        hovertemplate='<b>%{location}</b><br>' +
                      'Percentage Spent: %{z:.1%}<extra></extra>'
    ))

# Create a dropdown menu to toggle between traces
dropdown_buttons = []
for i, (col, title) in enumerate(columns):
    visibility = [False] * len(columns)
    visibility[i] = True  # Make the selected trace visible
    button = dict(
        label=title,
        method='update',
        args=[
            {'visible': visibility},
            # Remove title update since we're removing the title
        ]
    )
    dropdown_buttons.append(button)

# Update the figure layout with the dropdown
fig.update_layout(
    updatemenus=[
        dict(
            active=0,
            buttons=dropdown_buttons,
            direction='down',
            showactive=True,
            x=0.5,           # Center the dropdown
            xanchor='center',
            y=1.0,           # Position at the top
            yanchor='top',
            pad={"r": 10, "t": 10},
            type='dropdown',
            font=dict(
                size=24,      # Increase font size
                family="Castoro",
                color="black"
            ),
        )
    ],
    geo=dict(
        scope='usa',
        projection=go.layout.geo.Projection(type='albers usa')
    ),
    font=dict(
        family="Poppins",
        size=16,  # Default font size for the rest of the chart
        color="black"
    ),
    margin=dict(l=50, r=50, t=50, b=50)  # Adjust top margin since title is removed
)


# Display the figure
fig.write_html("./../figures/state_percent_esser_spent.html")
fig.show()

# %%

df_esser = pd.read_excel('./../data/raw/esser-federal-data.xlsx', sheet_name='arp') 
df_esser['isEsser3Mand20Tutoring'].mean()
# %%
