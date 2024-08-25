import streamlit as st
import pandas as pd
import plotly.express as px
import pickle

# Initialize session state for login
if 'login' not in st.session_state:
    st.session_state['login'] = False

# Function to display login page
def login_page():
    st.image('fractal_logo.png', width=150)  # Replace with your logo file path
    st.title("Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username == "mukherjees" and password == "123456":
            st.session_state['login'] = True
        else:
            st.error("Incorrect username or password")

# Main app logic
if st.session_state['login']:
    # Load data
    df = pd.read_excel('sample_data.xlsx')

    # Group by 'Market' and 'CapEx_Type' and aggregate the necessary columns
    grouped_df = df.groupby(['Market', 'CapEx_Type']).agg({
        'Historical_Spend_Million': 'sum',
        'Projected_Spend_Million': 'sum',
        'Expected_Asset_Lifespan_Years': 'sum',
        'Predicted_Risk_Percentage': 'sum',
        'NPV_Million': 'sum',
        'Priority_Score': 'sum',
        'Revenue_Impact_Million': 'sum',
        'Cost_Impact_Million': 'sum',
        'Margin_Impact_Million': 'sum'
    }).reset_index()

    # Initialize necessary columns if they don't exist
    if 'User input Spend' not in grouped_df.columns:
        grouped_df['User input Spend'] = 0.0
    if 'updated projected spend' not in grouped_df.columns:
        grouped_df['updated projected spend'] = grouped_df['Projected_Spend_Million'] + grouped_df['User input Spend']
    if 'New NPV' not in grouped_df.columns:
        grouped_df['New NPV'] = 0.0
    if 'New ROI' not in grouped_df.columns:
        grouped_df['New ROI'] = 0.0

    # Use st.cache_data or st.cache_resource instead of st.cache
    @st.cache_resource
    def load_encoder():
        with open('market_encoder.pkl', 'rb') as f:
            return pickle.load(f)

    @st.cache_resource
    def load_model():
        with open('ROI_Model.pkl', 'rb') as f:
            return pickle.load(f)

    # Main dashboard layout
    st.set_page_config(layout="wide")
    st.markdown(
        "<h6 style='text-align: right; color: grey;'>CapEx Dashboard</h6>",
        unsafe_allow_html=True
    )

    # Create a sidebar for filters
    st.sidebar.header("Filters")
    selected_market = st.sidebar.selectbox('Select Market', df['Market'].unique().tolist())
    selected_capex_type = st.sidebar.selectbox('Select CapEx Type', df['CapEx_Type'].unique().tolist())

    # Create a layout for the first page with two columns for DataFrames
    col1, col2 = st.columns([3, 1])

    with col1:
        st.write("### Base DataFrame")
        edited_df = st.data_editor(
            grouped_df,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_1"  # Unique key for this editor
        )
        
        # Recalculate 'updated projected spend' after user edits
        edited_df['updated projected spend'] = edited_df['Projected_Spend_Million'] + edited_df['User input Spend']
        
        # Display the updated dataframe after changes
        st.write("### Updated DataFrame")
        st.dataframe(edited_df, height=400,use_container_width=True)

    with col2:
        st.write("### ROI Optimization")
        
        # Load encoder and model
        market_encoder = load_encoder()
        roi_model = load_model()
        
        # Encode market names
        encoded_markets = market_encoder.transform(grouped_df['Market']).reshape(-1, 1)
        
        # Full list of features required by the model
        required_features = [
            'Encoded_Market', 'Projected_Spend_Million', 'Expected_Asset_Lifespan_Years',
            'Predicted_Risk_Percentage', 'NPV_Million', 'Priority_Score', 'Revenue_Impact_Million',
            'Cost_Impact_Million', 'Margin_Impact_Million',
            'Feature_10', 'Feature_11', 'Feature_12', 'Feature_13', 'Feature_14',
            'Feature_15', 'Feature_16', 'Feature_17', 'Feature_18', 'Feature_19',
            'Feature_20', 'Feature_21', 'Feature_22'
        ]
        
        # Initialize any missing features in grouped_df with default values
        for feature in required_features:
            if feature not in grouped_df.columns:
                grouped_df[feature] = 0  # Default value, adjust as necessary
        
        # Prepare model input with all required features
        model_input = pd.concat([pd.DataFrame(encoded_markets, columns=['Encoded_Market']), grouped_df[required_features[1:]]], axis=1)
        
        # Predict ROI
        grouped_df['Predicted_ROI'] = roi_model.predict(model_input)
        
        # Show total Projected and Historical Spend
        total_projected_spend = grouped_df['Projected_Spend_Million'].sum()
        total_historical_spend = grouped_df['Historical_Spend_Million'].sum()
        total_predicted_roi = grouped_df['Predicted_ROI'].sum()
        
        # Use HTML to display metrics with custom colors
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between;">
                <div style="background-color: #ffcccb; padding: 10px; margin: 5px; border-radius: 5px;">
                    <h4 style="color: red;">Historical Spend</h4>
                    <p>${total_historical_spend:.2f} Million</p>
                </div>
                <div style="background-color: #cce5ff; padding: 10px; margin: 5px; border-radius: 5px;">
                    <h4 style="color: blue;">Predicted ROI</h4>
                    <p>${total_predicted_roi:.2f} Million</p>
                </div>
                <div style="background-color: #d4edda; padding: 10px; margin: 5px; border-radius: 5px;">
                    <h4 style="color: green;">Projected Spend</h4>
                    <p>${total_projected_spend:.2f} Million</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Visualization Button
    if st.button('Generate Visualizations'):
        # Filter out non-positive values in Priority_Score
        filtered_df = edited_df[edited_df['Priority_Score'] > 0]
        
        # Plot 1: Historical Spend vs. Updated Projected Spend
        fig1 = px.bar(filtered_df, x='Market', y=['Historical_Spend_Million', 'updated projected spend'], barmode='group', title='Historical Spend vs. Updated Projected Spend')
        
        # Plot 2: Market-wise Bar Plot
        fig2 = px.bar(filtered_df, x='Market', y='updated projected spend', color='CapEx_Type', title='Market-wise Updated Projected Spend')
        
        # Plot 3: Scatter plot for NPV vs. Predicted Risk with a toggler for Market
        selected_market = st.selectbox('Select Market for NPV vs. Predicted Risk plot', filtered_df['Market'].unique())
        market_filtered_df = filtered_df[filtered_df['Market'] == selected_market]
        fig3 = px.scatter(market_filtered_df, x='NPV_Million', y='Predicted_Risk_Percentage', size='Priority_Score', color='CapEx_Type', title=f'NPV vs. Predicted Risk for {selected_market}')
        
        # Plot 4: Top 5 Markets by Updated Projected Spend
        top_5_markets = filtered_df.groupby('Market')['updated projected spend'].sum().nlargest(5).reset_index()
        fig4 = px.bar(top_5_markets, x='Market', y='updated projected spend', title='Top 5 Markets by Updated Projected Spend')
        
        # Display the plots
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)
        st.plotly_chart(fig3, use_container_width=True)
        st.plotly_chart(fig4, use_container_width=True)

    # Simulate Button
    if st.button('Simulate'):
        # Redirect to the next page
        st.write("### Simulation Results")
        
        # Display the small boxes for spend metrics (already included above)
        
        # Display the updated dataframe
        st.write("### Updated DataFrame with Simulation")
        st.data_editor(
            grouped_df,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_2"  # Unique key for this editor
        )
else:
    login_page()