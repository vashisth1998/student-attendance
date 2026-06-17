import streamlit as st
import pandas as pd

st.set_page_config(page_title="Attendance Tracker", layout="centered")
st.title("Attendance Tracker App 📊")
st.write("Apni Master Excel file aur Daily CSV files upload karein aur total attendance nikalein.")

st.subheader("1. Upload Master Data")
master_file = st.file_uploader("Master Excel File upload karein (xlsx/csv)", type=['xlsx', 'csv'])

st.subheader("2. Upload Daily Attendance")
daily_files = st.file_uploader("Daily CSV files upload karein", type=['csv'], accept_multiple_files=True)

if st.button("Calculate Attendance"):
    if master_file is not None and len(daily_files) > 0:
        try:
            # Master file load kar rahe hain (ab yeh CSV aur Excel dono handle karega)
            if master_file.name.endswith('.csv'):
                master_df = pd.read_csv(master_file)
            else:
                master_df = pd.read_excel(master_file)
            
            # Agar 'Total Attendance' column pehle se nahi hai toh naya banayein
            if 'Total Attendance' not in master_df.columns:
                master_df['Total Attendance'] = 0
            
            # NAYA SMART LOGIC FUNCTION
            def get_valid_names(row):
                name = str(row.get('Student Name', '')).replace('nan', '').strip().lower()
                p_id = str(row.get('pariticipant_id', '')).replace('nan', '').strip().lower() 
                
                last_3_digits = p_id[-3:] if len(p_id) >= 3 else p_id
                
                valid_names = [name]                                # 1. Exact Name
                valid_names.append(f"{name}-{last_3_digits}")       # 2. Full Name - ID
                
                # 3. First Name - ID (eg. 'akash-047' for 'akash kumar')
                first_name = name.split(" ")[0] if " " in name else name
                valid_names.append(f"{first_name}-{last_3_digits}")
                
                return valid_names

            for file in daily_files:
                daily_df = pd.read_csv(file)
                
                col_name = None
                for col in daily_df.columns:
                    if 'name' in col.lower() or 'participant' in col.lower():
                        col_name = col
                        break
                
                if col_name:
                    daily_df[col_name] = daily_df[col_name].fillna("")
                    raw_names = daily_df[col_name].astype(str).str.strip().str.lower().tolist()
                    
                    # NAYA: Underscore ko hyphen mein badalna aur spaces hatana
                    cleaned_attended_names = [
                        str(n).replace("_", "-").replace(" - ", "-").replace(" -", "-").replace("- ", "-") 
                        for n in raw_names
                    ]
                    
                    for index, row in master_df.iterrows():
                        valid_names = get_valid_names(row)
                        
                        # Partial match logic (taaki anjali_010 jaise easily catch ho jayein)
                        if any(any(v_name == d_name or v_name in d_name for d_name in cleaned_attended_names) for v_name in valid_names if v_name):
                            master_df.at[index, 'Total Attendance'] += 1
                else:
                    st.warning(f"File {file.name} mein 'Name' wala koi column nahi mila.")

            st.success("Attendance successfully calculate ho gayi hai! 🎉")
            st.dataframe(master_df) 

            csv = master_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Final Report",
                data=csv,
                file_name='Final_Attendance_Report.csv',
                mime='text/csv',
            )
            
        except Exception as e:
            st.error(f"Koi error aayi hai. Error details: {e}")
    else:
        st.warning("Pehle Master Excel file aur kam se kam ek Daily CSV file upload karein!")
