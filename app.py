# app.py
from flask import Flask, render_template, request
from amazon_paapi import AmazonApi

app = Flask(__name__)

# Dictionary of popular categories with browse node IDs
CATEGORIES = {
    'Electronics': '172282',
    'Computers': '565108',
    'Books': '283155',
    'Home & Kitchen': '1055398',
    'Beauty & Personal Care': '3760911',
    'Toys & Games': '165793011',
    'Sports & Outdoors': '3375251',
}

@app.route('/', methods=['GET'])
def index():
    # Updated with provided credentials
    ACCESS_KEY = 'AKPAVOAX6F1758423127'
    SECRET_KEY = 'fvDsfID7ikjBSAMqcUFsuu8ZxUGKXqZbTWkKODZp'
    PARTNER_TAG = 'naninaveennet-21'
    
    amazon = AmazonApi(
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        partner_tag=PARTNER_TAG,
        country='US'  # Change if needed, e.g., 'UK'
    )
    
    # Get category from query param, default to Electronics
    selected_category = request.args.get('category', 'Electronics')
    browse_node_id = CATEGORIES.get(selected_category, '172282')  # Fallback to Electronics
    
    # Search for items in selected category
    search_result = amazon.search_items(
        browse_node_id=browse_node_id,
        resources=[
            'ItemInfo.Title',
            'Images.Primary.Large',
        ],
        item_count=10  # Up to 10 items
    )
    
    asins = [item.asin for item in search_result.items if item.asin]
    
    if not asins:
        return render_template('index.html', deals=[], message="No items found.", categories=CATEGORIES, selected_category=selected_category)
    
    # Get detailed items with offers
    items_result = amazon.get_items(
        item_ids=asins,
        resources=[
            'ItemInfo.Title',
            'Images.Primary.Large',
            'Offers.Listings.Price',
            'Offers.Summaries.Savings',
            'Offers.Coupons',
        ]
    )
    
    deals = []
    for item in items_result.items:
        if hasattr(item.offers, 'listings') and item.offers.listings:
            listing = item.offers.listings[0]
            if hasattr(listing.price, 'amount') and listing.price.amount is not None:
                offer_price = listing.price.amount
                list_price = getattr(listing.price, 'list_price', None)
                discount_pct = 0
                discount_text = "Coupon Deal" if hasattr(item.offers, 'coupons') and item.offers.coupons else None
                if list_price and hasattr(list_price, 'amount') and list_price.amount:
                    discount_pct = ((list_price.amount - offer_price) / list_price.amount) * 100
                    if discount_pct > 20:
                        discount_text = f"{discount_pct:.1f}% off"
                        deal = {
                            'title': getattr(item.item_info.title, 'display_value', 'N/A'),
                            'image': getattr(item.images.primary.large, 'url', None) if hasattr(item.images, 'primary') else None,
                            'offer_price': f"${offer_price}",
                            'list_price': f"${list_price.amount}",
                            'discount': discount_text,
                            'url': getattr(item, 'detail_page_url', '#'),
                            'coupon': getattr(item.offers, 'coupons', None)
                        }
                        deals.append(deal)
                elif discount_text:  # Coupon only
                    deal = {
                        'title': getattr(item.item_info.title, 'display_value', 'N/A'),
                        'image': getattr(item.images.primary.large, 'url', None) if hasattr(item.images, 'primary') else None,
                        'offer_price': f"${offer_price}",
                        'list_price': f"${offer_price}",
                        'discount': discount_text,
                        'url': getattr(item, 'detail_page_url', '#'),
                        'coupon': item.offers.coupons
                    }
                    deals.append(deal)
    
    return render_template('index.html', deals=deals, message="No huge discounts found." if not deals else None, categories=CATEGORIES, selected_category=selected_category)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
