# app.py (fixed: removed 'resources' from search_items to avoid duplicate kwarg; fixed image/title access for safety)
from flask import Flask, render_template, request
from amazon_paapi import AmazonApi
import os

app = Flask(__name__)

# Updated categories with Amazon India browse node IDs
CATEGORIES = {
    'Electronics': '976420031',
    'Computers': '976393031',
    'Books': '976390031',
    'Home & Kitchen': '2454176031',
    'Beauty & Personal Care': '1350385031',
    'Toys & Games': '1350381031',
    'Sports & Outdoors': '1984444031',
}

@app.route('/', methods=['GET'])
def index():
    # Credentials (same, but now for IN)
    ACCESS_KEY = 'AKPAVOAX6F1758423127'
    SECRET_KEY = 'fvDsfID7ikjBSAMqcUFsuu8ZxUGKXqZbTWkKODZp'
    PARTNER_TAG = 'naninaveennet-21'
    
    # Updated for India
    amazon = AmazonApi(ACCESS_KEY, SECRET_KEY, PARTNER_TAG, 'IN')
    
    # Get category from query param, default to Electronics
    selected_category = request.args.get('category', 'Electronics')
    browse_node_id = CATEGORIES.get(selected_category, '976420031')  # Fallback to Electronics
    
    # Search for items in selected category (removed 'resources' to fix duplicate kwarg error; defaults should include ASIN/title/image)
    search_result = amazon.search_items(
        browse_node_id=browse_node_id,
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
                list_price_obj = getattr(listing.price, 'list_price', None)
                discount_pct = 0
                has_coupon = hasattr(item.offers, 'coupons') and item.offers.coupons
                discount_text = None
                
                if list_price_obj and hasattr(list_price_obj, 'amount') and list_price_obj.amount:
                    list_price = list_price_obj.amount
                    discount_pct = ((list_price - offer_price) / list_price) * 100
                    if discount_pct > 20:
                        discount_text = f"{discount_pct:.1f}% off"
                    elif has_coupon:
                        discount_text = f"{discount_pct:.1f}% off + Coupon"
                elif has_coupon:
                    discount_text = "Coupon Deal"
                
                if discount_text:  # Add if huge discount or coupon (regardless of discount %)
                    title = getattr(getattr(item.item_info.title, 'display_value', None), 'value', 'N/A') if hasattr(item.item_info, 'title') else 'N/A'
                    image_url = getattr(getattr(getattr(item.images, 'primary', None), 'large', None), 'url', None)
                    if hasattr(image_url, 'value'):
                        image_url = image_url.value
                    image = image_url if image_url else None
                    detail_url = getattr(item, 'detail_page_url', '#')
                    
                    deal = {
                        'title': title,
                        'image': image,
                        'offer_price': f"₹{offer_price}",
                        'list_price': f"₹{list_price}" if 'list_price' in locals() else f"₹{offer_price}",
                        'discount': discount_text,
                        'url': detail_url,
                        'coupon': item.offers.coupons if has_coupon else None
                    }
                    deals.append(deal)
    
    return render_template('index.html', deals=deals, message="No huge discounts found." if not deals else None, categories=CATEGORIES, selected_category=selected_category)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
