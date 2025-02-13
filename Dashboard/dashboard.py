import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style='dark')

class Visualization:
    def __init__(self, df):
        self.df = df

    def create_monthly_orders_df(self):
        monthly_orders_df = self.df.resample(rule='MS', on="order_purchase_timestamp").agg({
            "order_id": "nunique"
        }).reset_index()
    
        monthly_orders_df.rename(columns={
            "order_purchase_timestamp": "date",
            "order_id": "order_count"
        }, inplace=True)
    
        return monthly_orders_df

    def create_sum_order_items_df(self):
        sum_order_items_df = self.df.groupby("product_category_name_english")["product_id"].count().reset_index().sort_values(by="product_id", ascending=False)
        sum_order_items_df = sum_order_items_df.rename(columns={"product_id": "count", "product_category_name_english": "product"})
        return sum_order_items_df
    
    def create_bypaymenttype_df(self):
        bypaymenttype_df = self.df.groupby(by="payment_type_x").order_id.nunique().reset_index()
        bypaymenttype_df.rename(columns={
            "order_id": "customer_count"
        }, inplace=True)
        
        return bypaymenttype_df
    
    def create_category_trend_df(self):
        df = self.df.copy()  # Salin agar tidak mengubah df asli
        df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
        df.set_index('order_purchase_timestamp', inplace=True)
    
        category_trend_df = df.groupby([pd.Grouper(freq='M'), 'product_category_name_english'])['order_id'].count().reset_index()
    
        top_categories = df['product_category_name_english'].value_counts().nlargest(10).index
        category_trend_df = category_trend_df[category_trend_df['product_category_name_english'].isin(top_categories)]
    
        return category_trend_df


# Membaca dataset dengan cache agar lebih efisien
@st.cache_data
def load_data():
    df = pd.read_csv("all_data.csv")
    return df

all_df = load_data()
datetime_columns = ["shipping_limit_date", "review_creation_date","review_answer_timestamp","order_purchase_timestamp","order_approved_at","order_delivered_carrier_date","order_delivered_customer_date","order_estimated_delivery_date"]
all_df.sort_values(by="order_approved_at", inplace=True)
all_df.reset_index(drop=True, inplace=True)

for column in datetime_columns:
   all_df[column] = pd.to_datetime(all_df[column], format="%Y-%m-%d %H:%M:%S", errors='coerce')

# Membuat komponen filter
min_date = all_df["order_approved_at"].min()
max_date = all_df["order_approved_at"].max()

with st.sidebar:
    
    st.title("Ahmad Fauzan")
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")

    start_date, end_date = st.date_input(
        label="Rentang Waktu", 
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[
    (all_df["order_approved_at"] >= pd.to_datetime(start_date)) & 
    (all_df["order_approved_at"] <= pd.to_datetime(end_date))
]

# Inisialisasi objek Visualization dengan main_df
vis = Visualization(main_df)
monthly_order_df = vis.create_monthly_orders_df()
sum_order_items_df = vis.create_sum_order_items_df()
by_payment_type_df = vis.create_bypaymenttype_df()
category_trend_df = vis.create_category_trend_df()

st.header('Proyek Analisis Data :sparkles:')
st.subheader('Monthly Orders')

col1, col2 = st.columns(2)

with col1:
    year=start_date.strftime("%Y")
    monthly_orders_2018_df = monthly_order_df[monthly_order_df['date'].astype(str).str.startswith(year)]
    total_orders = monthly_orders_2018_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    st.metric("Year", value=year)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    monthly_orders_2018_df["date"],
    monthly_orders_2018_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
 
st.pyplot(fig)

#Best and worst product
st.subheader("Best and Worst Product by Number of Sales")
 
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))
 
colors = ["#1aa3e9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
 
sns.barplot(x="count", y="product", hue="product", data=sum_order_items_df.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x="count", y="product", hue="product", data=sum_order_items_df.sort_values(by="count", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)
 
st.pyplot(fig)
 
# Payment Type
st.subheader("Payment Type")
fig, ax = plt.subplots(figsize=(20, 10))
sns.barplot(
    y="customer_count", 
    x="payment_type_x",
    hue="payment_type_x",
    data=by_payment_type_df,
    palette=colors,
    ax=ax
)
ax.set_title("Number of Customer by Payment Type", loc="center", fontsize=50)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='x', labelsize=35)
ax.tick_params(axis='y', labelsize=30)
st.pyplot(fig)

#Trend Category
st.subheader("Tren Penjualan Produk per Bulan (Top 10 Kategori)")

# Plot grafik menggunakan Matplotlib
fig, ax = plt.subplots(figsize=(16, 6))

for category in category_trend_df['product_category_name_english'].unique():
    data = category_trend_df[category_trend_df['product_category_name_english'] == category]
    ax.plot(data['order_purchase_timestamp'], data['order_id'], marker='o', label=category)

# Format tampilan grafik
ax.set_xlabel("Tahun/Bulan")
ax.set_ylabel("Jumlah Pesanan")
ax.set_title("Tren Penjualan Produk per Bulan (Top 10 Kategori)")
ax.legend(title="Kategori Produk", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.xticks(rotation=45)

st.pyplot(fig)
