import streamlit as st
import pandas as pd

st.set_page_config(page_title="Attendance Tracker", layout="centered")
st.title("Attendance Tracker App 📊")
st.write("Apni Master Excel file aur Daily CSV files upload karein aur total attendance nikalein.")

# 1. Upload Files
st.subheader("1. Upload Master Data")
master_file = st.file_uploader("Master Excel File upload karein (xlsx)", type=['xlsx'])

st.subheader("2. Upload Daily Attendance")
daily_files = st.file_uploader("Daily CSV files upload karein", type=['csv'], accept_multiple_files=True)

# 2. Logic & Calculation
if st.button("Calculate Attendance"):
    if master_file is not None and len(daily_files) > 0:
        try:
            # Master file load kar rahe hain
            master_df = pd.read_excel(master_file)
            
            # Agar 'Total Attendance' column pehle se nahi hai toh naya banayein
            master_df['Total Attendance'] = 0
            
            # Master file ke valid names generate karna
            def get_valid_names(row):
                name = str(row.get('Student Name', '')).strip().lower()
                p_id = str(row.get('pariticipant_id', '')).strip().lower() 
                
                last_3_digits = p_id[-3:] if len(p_id) >= 3 else p_id
                
                # Standard format without spaces around hyphen
                name_with_id = f"{name}-{last_3_digits}"
                
                return [name, name_with_id]

            # Daily files check kar rahe hain
            for file in daily_files:
                daily_df = pd.read_csv(file)
                
                # Column name dhoondna (Participant Name ya Name)
                col_name = None
                for col in daily_df.columns:
                    if 'name' in col.lower() or 'participant' in col.lower():
                        col_name = col
                        break
                
                if col_name:
                    # Daily CSV ke names ko lower case mein karke list banana
                    raw_names = daily_df[col_name].astype(str).str.strip().str.lower().tolist()
                    
                    # Hyphen ke aaspas ke saare extra spaces hatana (Normalizing)
                    # "aditya - 058", "aditya -058", "aditya- 058" sab "aditya-058" ban jayenge
                    cleaned_attended_names = [
                        name.replace(" - ", "-").replace(" -", "-").replace("- ", "-") 
                        for name in raw_names
                    ]
                    
                    # Attendance Match karna
                    for index, row in master_df.iterrows():
                        valid_names = get_valid_names(row)
                        
                        # Agar exact name ya name-id milta hai
                        if any(v_name in cleaned_attended_names for v_name in valid_names):
                            master_df.at[index, 'Total Attendance'] += 1
                else:
                    st.warning(f"File {file.name} mein 'Name' wala koi column nahi mila.")

            st.success("Attendance successfully calculate ho gayi hai! 🎉")
            
            # App par result dikhane ke liye
            st.dataframe(master_df) 

            # 3. Download ka button
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
