import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Battery Cell Monitor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .critical-alert {
        background: #ffe6e6;
        border: 2px solid #ff4444;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .warning-alert {
        background: #fff3cd;
        border: 2px solid #ffc107;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'cell_types' not in st.session_state:
    st.session_state.cell_types = {
        "LFP": {
            "name": "Lithium Iron Phosphate",
            "nominal_voltage": 3.2,
            "minimum_voltage": 2.8,
            "maximum_voltage": 3.6,
            "charge_time": 90,
            "discharge_time": 180
        },
        "NMC": {
            "name": "Nickel Manganese Cobalt",
            "nominal_voltage": 3.6,
            "minimum_voltage": 3.2,
            "maximum_voltage": 4.0,
            "charge_time": 120,
            "discharge_time": 240
        }
    }

if 'cells_data' not in st.session_state:
    st.session_state.cells_data = []

if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False

if 'bench_info' not in st.session_state:
    st.session_state.bench_info = {'name': '', 'group': ''}

# Helper functions
def generate_cell_data(cell_type):
    """Generate realistic cell data"""
    specs = st.session_state.cell_types[cell_type]
    
    base_voltage = specs["nominal_voltage"]
    voltage_variation = np.random.uniform(-0.1, 0.1)
    voltage = max(specs["minimum_voltage"], 
                  min(specs["maximum_voltage"], 
                      base_voltage + voltage_variation))
    
    current = max(0.1, 0.8 + np.random.uniform(-0.2, 0.3))
    temperature = np.random.uniform(25, 45)
    capacity = voltage * current
    
    voltage_range = specs["maximum_voltage"] - specs["minimum_voltage"]
    soc = ((voltage - specs["minimum_voltage"]) / voltage_range) * 100
    
    return {
        'voltage': round(voltage, 2),
        'current': round(current, 2),
        'temperature': round(temperature, 1),
        'capacity': round(capacity, 2),
        'soc': round(soc, 1)
    }

def get_cell_status(voltage, temperature, cell_type):
    """Determine cell status"""
    specs = st.session_state.cell_types[cell_type]
    
    if voltage <= specs["minimum_voltage"] * 1.1 or temperature > 45:
        return "🚨 Critical", "red"
    elif voltage <= specs["minimum_voltage"] * 1.2 or temperature > 40:
        return "⚠️ Warning", "orange"
    elif voltage >= specs["maximum_voltage"] * 0.9:
        return "🔋 High", "green"
    else:
        return "🟢 Normal", "blue"

def create_gauge_chart(value, title, min_val, max_val, unit=""):
    """Create a gauge chart"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': (min_val + max_val) / 2},
        gauge = {
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [min_val, min_val + (max_val - min_val) * 0.3], 'color': "lightgray"},
                {'range': [min_val + (max_val - min_val) * 0.3, min_val + (max_val - min_val) * 0.7], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_val * 0.9
            }
        },
        number = {'suffix': unit}
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# Main header
st.markdown("""
<div class="main-header">
    <h1>⚡ Advanced Battery Cell Monitoring System</h1>
    <p>Real-time monitoring with customizable cell configurations</p>
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("🔧 Configuration")
    
    # Bench information
    st.subheader("Bench Information")
    bench_name = st.text_input("Bench Name", value=st.session_state.bench_info['name'])
    group_number = st.text_input("Group Number", value=st.session_state.bench_info['group'])
    st.session_state.bench_info = {'name': bench_name, 'group': group_number}
    
    st.divider()
    
    # Cell type management
    st.subheader("Cell Type Management")
    
    # Add new cell type
    with st.expander("Add Custom Cell Type"):
        new_type_key = st.text_input("Cell Type Code (e.g., 'LCO')")
        new_type_name = st.text_input("Cell Type Name")
        col1, col2 = st.columns(2)
        with col1:
            min_volt = st.number_input("Min Voltage (V)", value=2.8, step=0.1)
            nom_volt = st.number_input("Nominal Voltage (V)", value=3.7, step=0.1)
        with col2:
            max_volt = st.number_input("Max Voltage (V)", value=4.2, step=0.1)
            charge_time = st.number_input("Charge Time (min)", value=100, step=10)
        discharge_time = st.number_input("Discharge Time (min)", value=200, step=10)
        
        if st.button("Add Cell Type") and new_type_key and new_type_name:
            st.session_state.cell_types[new_type_key.upper()] = {
                "name": new_type_name,
                "nominal_voltage": nom_volt,
                "minimum_voltage": min_volt,
                "maximum_voltage": max_volt,
                "charge_time": charge_time,
                "discharge_time": discharge_time
            }
            st.success(f"Added {new_type_key.upper()} cell type!")
            st.rerun()
    
    # Edit existing cell types
    with st.expander("Edit Cell Types"):
        selected_type = st.selectbox("Select Cell Type", list(st.session_state.cell_types.keys()))
        if selected_type:
            specs = st.session_state.cell_types[selected_type]
            
            new_name = st.text_input("Name", value=specs["name"])
            col1, col2 = st.columns(2)
            with col1:
                new_min = st.number_input("Min V", value=specs["minimum_voltage"], step=0.1)
                new_nom = st.number_input("Nominal V", value=specs["nominal_voltage"], step=0.1)
            with col2:
                new_max = st.number_input("Max V", value=specs["maximum_voltage"], step=0.1)
                new_charge = st.number_input("Charge (min)", value=specs["charge_time"], step=10)
            new_discharge = st.number_input("Discharge (min)", value=specs["discharge_time"], step=10)
            
            if st.button("Update Cell Type"):
                st.session_state.cell_types[selected_type] = {
                    "name": new_name,
                    "nominal_voltage": new_nom,
                    "minimum_voltage": new_min,
                    "maximum_voltage": new_max,
                    "charge_time": new_charge,
                    "discharge_time": new_discharge
                }
                st.success("Cell type updated!")
                st.rerun()
    
    st.divider()
    
    # Cell management
    st.subheader("Cell Management")
    
    # Add new cell
    with st.expander("Add New Cell"):
        cell_name = st.text_input("Cell Name", value=f"Cell_{len(st.session_state.cells_data) + 1}")
        cell_type = st.selectbox("Cell Type", list(st.session_state.cell_types.keys()))
        
        if st.button("Add Cell"):
            new_cell = {
                'id': len(st.session_state.cells_data),
                'name': cell_name,
                'type': cell_type,
                'timestamp': datetime.now(),
                **generate_cell_data(cell_type)
            }
            st.session_state.cells_data.append(new_cell)
            st.success(f"Added {cell_name}!")
            st.rerun()
    
    # Monitoring controls
    st.subheader("Monitoring Controls")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔴 Start Monitor" if not st.session_state.monitoring_active else "⏸️ Stop Monitor"):
            st.session_state.monitoring_active = not st.session_state.monitoring_active
            st.rerun()
    
    with col2:
        if st.button("🔄 Update Data"):
            for i, cell in enumerate(st.session_state.cells_data):
                st.session_state.cells_data[i].update(generate_cell_data(cell['type']))
                st.session_state.cells_data[i]['timestamp'] = datetime.now()
            st.rerun()
    
    # Auto-refresh
    if st.session_state.monitoring_active:
        st.info("🔄 Auto-refresh active (every 3 seconds)")
        time.sleep(3)
        for i, cell in enumerate(st.session_state.cells_data):
            st.session_state.cells_data[i].update(generate_cell_data(cell['type']))
            st.session_state.cells_data[i]['timestamp'] = datetime.now()
        st.rerun()

# Main content area
if not st.session_state.cells_data:
    st.info("👈 Add some cells from the sidebar to start monitoring!")
else:
    # Critical alerts
    critical_cells = []
    warning_cells = []
    
    for cell in st.session_state.cells_data:
        status, color = get_cell_status(cell['voltage'], cell['temperature'], cell['type'])
        if "Critical" in status:
            critical_cells.append(cell)
        elif "Warning" in status:
            warning_cells.append(cell)
    
    if critical_cells:
        st.markdown("""
        <div class="critical-alert">
            <h3>🚨 Critical Alerts</h3>
        """, unsafe_allow_html=True)
        for cell in critical_cells:
            st.error(f"**{cell['name']}**: {cell['voltage']}V, {cell['temperature']}°C - Immediate attention required!")
        st.markdown("</div>", unsafe_allow_html=True)
    
    if warning_cells:
        st.markdown("""
        <div class="warning-alert">
            <h3>⚠️ Warnings</h3>
        """, unsafe_allow_html=True)
        for cell in warning_cells:
            st.warning(f"**{cell['name']}**: {cell['voltage']}V, {cell['temperature']}°C - Monitor closely")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Summary metrics
    st.subheader("📊 System Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Cells", len(st.session_state.cells_data))
    
    with col2:
        avg_voltage = np.mean([cell['voltage'] for cell in st.session_state.cells_data])
        st.metric("Avg Voltage", f"{avg_voltage:.2f}V")
    
    with col3:
        avg_temp = np.mean([cell['temperature'] for cell in st.session_state.cells_data])
        st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
    
    with col4:
        total_capacity = sum([cell['capacity'] for cell in st.session_state.cells_data])
        st.metric("Total Capacity", f"{total_capacity:.2f}Wh")
    
    with col5:
        avg_soc = np.mean([cell['soc'] for cell in st.session_state.cells_data])
        st.metric("Avg SOC", f"{avg_soc:.1f}%")
    
    # Detailed cell view
    st.subheader("🔋 Individual Cell Status")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Table View", "📈 Charts", "🎛️ Gauges"])
    
    with tab1:
        # Convert to DataFrame for better display
        df_data = []
        for cell in st.session_state.cells_data:
            status, color = get_cell_status(cell['voltage'], cell['temperature'], cell['type'])
            specs = st.session_state.cell_types[cell['type']]
            
            df_data.append({
                'Cell Name': cell['name'],
                'Type': cell['type'],
                'Voltage (V)': cell['voltage'],
                'Current (A)': cell['current'],
                'Temperature (°C)': cell['temperature'],
                'Capacity (Wh)': cell['capacity'],
                'SOC (%)': cell['soc'],
                'Status': status,
                'Charge Time (min)': specs['charge_time'],
                'Discharge Time (min)': specs['discharge_time'],
                'Last Updated': cell['timestamp'].strftime('%H:%M:%S')
            })
        
        df = pd.DataFrame(df_data)
        
        # Color code the dataframe
        def highlight_status(row):
            if '🚨' in row['Status']:
                return ['background-color: #ffebee'] * len(row)
            elif '⚠️' in row['Status']:
                return ['background-color: #fff3e0'] * len(row)
            elif '🔋' in row['Status']:
                return ['background-color: #e8f5e8'] * len(row)
            else:
                return [''] * len(row)
        
        st.dataframe(df.style.apply(highlight_status, axis=1), use_container_width=True)
    
    with tab2:
        if len(st.session_state.cells_data) > 0:
            # Voltage chart
            fig_voltage = px.bar(
                df, 
                x='Cell Name', 
                y='Voltage (V)',
                color='Type',
                title='Cell Voltages',
                hover_data=['Status', 'Temperature (°C)']
            )
            st.plotly_chart(fig_voltage, use_container_width=True)
            
            # Temperature vs SOC scatter plot
            fig_scatter = px.scatter(
                df,
                x='Temperature (°C)',
                y='SOC (%)',
                size='Capacity (Wh)',
                color='Type',
                hover_name='Cell Name',
                title='Temperature vs State of Charge'
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
    
    with tab3:
        # Create gauge charts for selected cell
        selected_cell_name = st.selectbox("Select Cell for Detailed View", [cell['name'] for cell in st.session_state.cells_data])
        selected_cell = next(cell for cell in st.session_state.cells_data if cell['name'] == selected_cell_name)
        specs = st.session_state.cell_types[selected_cell['type']]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig_volt = create_gauge_chart(
                selected_cell['voltage'], 
                "Voltage", 
                specs['minimum_voltage'], 
                specs['maximum_voltage'], 
                "V"
            )
            st.plotly_chart(fig_volt, use_container_width=True)
        
        with col2:
            fig_temp = create_gauge_chart(
                selected_cell['temperature'], 
                "Temperature", 
                20, 
                50, 
                "°C"
            )
            st.plotly_chart(fig_temp, use_container_width=True)
        
        with col3:
            fig_soc = create_gauge_chart(
                selected_cell['soc'], 
                "State of Charge", 
                0, 
                100, 
                "%"
            )
            st.plotly_chart(fig_soc, use_container_width=True)
        
        # Cell details
        status, color = get_cell_status(selected_cell['voltage'], selected_cell['temperature'], selected_cell['type'])
        
        st.subheader(f"📋 {selected_cell['name']} Details")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"""
            **Cell Type**: {specs['name']}  
            **Current**: {selected_cell['current']}A  
            **Capacity**: {selected_cell['capacity']}Wh  
            **Status**: {status}
            """)
        
        with col2:
            st.info(f"""
            **Voltage Range**: {specs['minimum_voltage']}V - {specs['maximum_voltage']}V  
            **Charge Time**: {specs['charge_time']} minutes  
            **Discharge Time**: {specs['discharge_time']} minutes  
            **Last Updated**: {selected_cell['timestamp'].strftime('%H:%M:%S')}
            """)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🔋 Advanced Battery Cell Monitoring System | Built with Streamlit</p>
    <p>Bench: <strong>{}</strong> | Group: <strong>{}</strong> | Cells: <strong>{}</strong> | Status: <strong>{}</strong></p>
</div>
""".format(
    bench_name or "Not Set", 
    group_number or "Not Set", 
    len(st.session_state.cells_data),
    "🟢 Monitoring Active" if st.session_state.monitoring_active else "⏸️ Monitoring Paused"
), unsafe_allow_html=True)