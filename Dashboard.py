import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pickle

# Set page config as the very first command
st.set_page_config(layout="wide")

# Initialize session state for login and page navigation
if 'login' not in st.session_state:
    st.session_state['login'] = False
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'  # Default page is 'home'

# Define custom styles for the container
def set_container_style(background_color, border_color):
    return f'''
    <style>
    .custom-container {{
        background-color: {background_color};
        border: 5px solid {border_color};
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 20px;
    }}
    </style>
    '''

# Function to display the login page
def login_page():
    st.image('shell_logo.png', width=100)  # Update with your logo file path
    st.markdown("<h1 style='text-align: center; color: red;'>GLOBAL CAPEX PLANNING</h1>", unsafe_allow_html=True)
    
    with st.form(key='login_form'):
        st.markdown("### Login")
        username = st.text_input("Email ID")
        password = st.text_input("Password", type="password")
        remember_me = st.checkbox("Remember Me")
        submit_button = st.form_submit_button(label='Log in')
        
        if submit_button:
            if username == "mukherjees" and password == "123456":
                st.session_state['login'] = True
                st.session_state['username'] = username
            else:
                st.error("Incorrect username or password")
    
    st.markdown("<a href='#' style='color: red;'>Login with SSO</a>", unsafe_allow_html=True)

# Function to display the home page
def home_page():
    st.markdown(f"### Hi {st.session_state['username']}, Welcome to the Global Capex Planning tool!")
    if st.button("Go to Dashboard"):
        st.session_state['page'] = 'dashboard'

# Main app logic
if st.session_state['login']:
    # Add top left corner navigation and top right username display
    col1, col2 = st.columns([4, 1])
    with col1:
        st.image('shell_logo_header.png', width=1000)  # Add logo to the dashboard page
        st.markdown("[Home](#) -> Sheet1")
    with col2:
        st.markdown(f"Logged in as: **{st.session_state['username']}**", unsafe_allow_html=True)

    if st.session_state['page'] == 'home':
        home_page()
    else:
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

        # Cache data loading functions
        @st.cache_resource
        def load_encoder():
            with open('market_encoder.pkl', 'rb') as f:
                return pickle.load(f)

        @st.cache_resource
        def load_model():
            with open('ROI_Model.pkl', 'rb') as f:
                return pickle.load(f)

        # Main dashboard layout
        st.markdown("<h6 style='text-align: middle ; color: red;'>Shell Global CapEx Dashboard</h6>", unsafe_allow_html=True)
        # # Main dashboard layout
        # col1, col2 = st.columns([0.1, 3])  # Adjust column widths for the logo and the title text

        # with col1:
        #     st.image('shell_logo.png', width=50)  # Add Shell logo with specified width

        # with col2:
        #     st.markdown(
        #         "<h2 style='text-align: left; color: grey; margin-top: 0;'>Shell CapEx Dashboard</h2>", 
        #         unsafe_allow_html=True
        #     )


        # Create a sidebar for filters
        st.sidebar.header("Filters")
        selected_market = st.sidebar.selectbox('Select Market', df['Market'].unique().tolist())
        selected_capex_type = st.sidebar.selectbox('Select CapEx Type', df['CapEx_Type'].unique().tolist())

        # Load encoder and model
        market_encoder = load_encoder()
        roi_model = load_model()

        # Encode market names
        encoded_markets = market_encoder.transform(grouped_df['Market']).reshape(-1, 1)

        # Full list of features required by the model
        required_features = [
            'Encoded_Market', 'Projected_Spend_Million', 'Expected_Asset_Lifespan_Years', 
            'Predicted_Risk_Percentage', 'NPV_Million', 'Priority_Score', 'Revenue_Impact_Million', 
            'Cost_Impact_Million', 'Margin_Impact_Million', 'Feature_10', 'Feature_11', 'Feature_12', 
            'Feature_13', 'Feature_14', 'Feature_15', 'Feature_16', 'Feature_17', 'Feature_18', 
            'Feature_19', 'Feature_20', 'Feature_21', 'Feature_22'
        ]

        # Initialize any missing features in grouped_df with default values
        for feature in required_features:
            if feature not in grouped_df.columns:
                grouped_df[feature] = 0  # Default value, adjust as necessary

        # Prepare model input with all required features
        model_input = pd.concat([pd.DataFrame(encoded_markets, columns=['Encoded_Market']), grouped_df[required_features[1:]]], axis=1)

        # Predict ROI
        grouped_df['Predicted_ROI'] = roi_model.predict(model_input)

        # Show total metrics
        total_projected_spend = grouped_df['Projected_Spend_Million'].sum()
        total_historical_spend = grouped_df['Historical_Spend_Million'].sum()
        total_predicted_roi = grouped_df['Predicted_ROI'].sum()
        total_market_count = grouped_df['Market'].nunique()
        total_capex_count = grouped_df['CapEx_Type'].nunique()
        total_cost_impact = grouped_df['Cost_Impact_Million'].sum()
        total_historical_spend_billion = total_historical_spend / 1000
        total_projected_spend_billion = total_projected_spend / 1000

        # Display metrics with custom colors
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between;">
                <div style="background-color: #ffcccb; padding: 10px; margin: 5px; border-radius: 5px;">
                    <h4 style="color: red;">Requested Allocation</h4>
                    <p>${round(total_historical_spend_billion)} Billion</p>
                </div>
                <div style="background-color: #d4edda; padding: 10px; margin: 5px; border-radius: 5px;">
                    <h4 style="color: green;">Actual Allocation</h4>
                    <p>${round(total_projected_spend_billion)} Billion</p>
                </div>
                <div style="background-color: #d4edda; padding: 10px; margin: 5px; border-radius: 5px;">
                    <h4 style="color: green;">Predicted ROI</h4>
                    <p>2.08%</p>
                </div>
                <div style="background-color: #d4edda; padding: 10px; margin: 5px; border-radius: 5px;">
                    <h4 style="color: green;">Total Market Count</h4>
                    <p>{30}</p>
                </div>
                <div style="background-color: #d4edda; padding: 10px; margin: 5px; border-radius: 5px;">
                    <h4 style="color: green;">Total CapEx Count</h4>
                    <p>{total_capex_count}</p>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

        # Generate and show visualizations in two rows
        filtered_df = grouped_df[grouped_df['Priority_Score'] > 0]

        # Plot 1: Top 5 Markets by Projected Spend
        top_5_markets_spend = filtered_df.groupby('Market')['Projected_Spend_Million'].sum().nlargest(5).reset_index()
        fig1 = px.bar(top_5_markets_spend, x='Market', y='Projected_Spend_Million', title='Top 5 Markets by Projected Spend')

        # Plot 2: Historical Spend vs. Updated Projected Spend (Top 5 Markets)
        top_5_markets_spend = filtered_df[filtered_df['Market'].isin(top_5_markets_spend['Market'])]
        fig2 = px.bar(top_5_markets_spend, x='Market', y=['Historical_Spend_Million', 'updated projected spend'], 
                      title='Historical Spend vs. Updated Projected Spend (Top 5 Markets)')

        # Plot 3: NPV vs. ROI
        #fig3 = px.scatter(filtered_df, x='NPV_Million', y='Predicted_ROI', 
         #                 title='NPV vs. Predicted ROI')
         # Plot 3: Scatter plot for NPV vs. Predicted ROI with a market filter and CapEx Type legend
        selected_market_for_plot = st.selectbox('Select Market for NPV vs. Predicted ROI plot', filtered_df['Market'].unique())

        # Filter the dataframe based on the selected market
        market_filtered_df_for_plot = filtered_df[filtered_df['Market'] == selected_market_for_plot]
    
        # Create scatter plot with color differentiation by CapEx Type
        fig3 = px.scatter(
            market_filtered_df_for_plot,
            x='NPV_Million',
            y='Predicted_ROI',
            color='CapEx_Type',  # Adding CapEx_Type to color for legend
            title=f'NPV vs. Predicted ROI for {selected_market_for_plot}',
            labels={'NPV_Million': 'Net Present Value (Million)', 'Predicted_ROI': 'Predicted ROI (%)'}
        )

        # Plot 4: Feature Importance Plot
        feature_importances = roi_model.feature_importances_ if hasattr(roi_model, 'feature_importances_') else [0] * len(required_features)
        feature_df = pd.DataFrame({'Feature': required_features, 'Importance': feature_importances})
        feature_df = feature_df.sort_values(by='Importance', ascending=False).head(9)
        fig4 = px.bar(feature_df, x='Importance', y='Feature', orientation='h', title='Top 10 Features')

        # Display plots in two rows
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig1)
            st.plotly_chart(fig2)
        with col2:
            st.plotly_chart(fig3)
            st.plotly_chart(fig4)
        
        st.markdown(
                        """
                        <style>
                        .container {
                            background-color: yellow;
                            border: 5px solid red;
                            border-radius: 10px;
                            padding: 15px;
                            margin-bottom: 20px;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True
                    )
        with st.container():
                #st.markdown('<div class="container">', unsafe_allow_html=True)
                st.write("Market-wise DataFrame")
                st.dataframe(grouped_df)
                st.markdown('</div>', unsafe_allow_html=True)

        # Apply styles for the second DataFrame (Overall DataFrame)
        # st.markdown(set_container_style('yellow', 'red'), unsafe_allow_html=True)
        with st.container():
            #st.markdown('<div class="container">', unsafe_allow_html=True)
            st.write("Customer Grid")
            st.dataframe(df)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Simulate Button
            if st.button('Simulate', key="simulate", help="Click to simulate"):
                # Redirect to the next page
                st.write("### Simulation Results")
                
                # Display the updated dataframe
                st.write("### Updated Da    taFrame with Simulation")
                st.data_editor(
                    grouped_df,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="editor_2"  # Unique key for this editor
                )

                st.markdown(
                    """
                    <style>
                    .button-custom {
                        background-color: blue;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        text-align: center;
                        text-decoration: none;
                        display: inline-block;
                        font-size: 16px;
                        margin: 4px 2px;
                        cursor: pointer;
                        border-radius: 4px;
                    }
                    </style>
                    <a href="#" class="button-custom" onclick="document.querySelector('[data-testid=stButton][data-key=simulate]').click()">Simulate</a>
                    """,
                    unsafe_allow_html=True
                )


else:
    login_page()