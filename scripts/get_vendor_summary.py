import sqlite3
import pandas as pd
import logging
from ingestion_db import ingest_db

logging.basicConfig(
    filename="logs/get_vendor_summary.log",
    level= logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

def create_vendor_summary(conn):
    '''this function will merge the different tables to get the overall vendor summary and adds new columns in the resultant data'''
    vendor_sales_summary = pd.read_sql_query("""with freightSummary as (
                select 
                    vendorNumber,
                    sum(freight) as freightCost
                from vendor_invoice
                group by vendorNumber
            ),
            
            purchaseSummary as (
                select
                    p.vendorNumber,
                    p.vendorName,
                    p.description,
                    p.Brand,
                    p.purchasePrice,
                    pp.volume,
                    pp.price as actualPrice,
                    sum(p.quantity) as totalPurchaseQuantity,
                    sum(p.Dollars) as totalPurchaseDollars
                from purchases p
                join purchase_prices pp
                    on p.brand = pp.brand
                where p.purchasePrice > 0
                group by p.vendorNumber, p.vendorName, p.Brand
            ),
            
            salesSummary as (
                select
                    vendorNo,
                    Brand,
                    sum(salesDollars) as totalSalesDollars,
                    sum(salesPrice) as totalSalesPrice,
                    sum(SalesQuantity) as totalSalesQuantity,
                    sum(ExciseTax) as totalExciseTax
                from sales
                group by vendorNo, Brand    
            )
            
            select 
                ps.vendorNumber,
                ps.vendorName,
                ps.brand,
                ps.description,
                ps.purchasePrice,
                ps.actualPrice,
                ps.volume,
                ps.totalPurchaseQuantity,
                ps.totalPurchaseDollars,
                ss.totalSalesQuantity,
                ss.totalSalesDollars,
                ss.totalSalesPrice,
                ss.totalExciseTax,
                fs.freightCost
            from purchaseSummary ps
            left join salesSummary ss
                on ps.vendorNumber = ss.vendorNo
                and ps.brand = ss.brand
            left join freightSummary fs
                on ps.vendorNumber = fs.vendorNumber
            order by ps.totalPurchaseDollars desc
            """, conn)
    return vendor_sales_summary

def clean_data(df):
    '''this will clean the data'''
    df['volume'] = df['volume'].astype('float64')
    df.fillna(0, inplace =True)
    df['vendorName'] = df['vendorName'].str.strip()
    df['description'] = df['description'].str.strip()
    
    # creating new columns
    vendor_sales_summary['grossProfit'] = vendor_sales_summary['totalSalesDollars'] -vendor_sales_summary['totalPurchaseDollars']
    vendor_sales_summary['profitMargin'] = (vendor_sales_summary['grossProfit'] / vendor_sales_summary['totalSalesDollars'])*100
    vendor_sales_summary['stockTurnover'] = vendor_sales_summary['totalSalesQuantity']/vendor_sales_summary['totalPurchaseQuantity']
    vendor_sales_summary['salestoPurchaseRatio'] = vendor_sales_summary['totalSalesDollars']/vendor_sales_summary['totalPurchaseDollars']
    return df


if __name__ == '__main__':
    #create db connection
    conn = sqlite3.connect('inventory.db')
    logging.info('Creating vendor summary table.......')
    summary_df = create_vendor_summary(conn)
    logging.info(summary_df.head())

    logging.info('Cleaning data......')
    clead_df = clean_data(summary_df)
    logging.info(clean_df.head())
    
    logging.info('ingesting data......')
    ingest_db(clean_df,'vendor_sales_summary',conn)
    logging.info('completed')






























