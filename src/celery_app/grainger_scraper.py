from camoufox.async_api import AsyncCamoufox
import traceback
from random import randint


def check_product_stock(content):
    if any([x.lower() in content.lower() for x in [
        "Sorry we're having difficulty finding a match for the term(s) you've entered. You can also search for products using other keywords and item numbers.",
        "Product is Discontinued", "Product Is Temporarily Unavailable for Purchase","This product is no longer in stock"]]):
        return True


async def save_resources(route, request):
    if request.resource_type in ["image", "media", "font", "stylesheet"]:
        print("Blocked")
        await route.abort()
    else:
        await route.continue_()

async def run_scrape(url, zipcode):
    pid = url.split("?")[0].split("/")[-1].split("-")[-1]
    async with AsyncCamoufox(
            humanize=2.0,
            os=["windows", "linux"],
            headless="virtual",
            geoip=True,
            proxy={
                "server": "geo.iproyal.com:12321",
                "username": "RAD5VCH0WnT6glQG",
                "password": "uJUnzLRMv5c5Ap0Z_country-us",
            },
        ) as browser:
        try:
            page = await browser.new_page()
            
            res = await page.goto(url, wait_until="load")

            first_content = await page.content()

            try:#404 page url:https://www.grainger.com/product/575562
                await page.wait_for_selector('#modernized-gcom-error',timeout=5000)
                if await page.locator('#modernized-gcom-error h2:has-text("Unable to complete your request")').is_visible():
                    return first_content, "", 404
            except:
                pass

            if check_product_stock(first_content):
                return first_content, "", 200

            try:#Discontinued
                await page.wait_for_selector("div[data-testid='notification-discontinued']", timeout=10000)
                return first_content, "", 200
            except:
                pass

            try:
                await page.wait_for_selector("button:has-text('Change')", timeout=10000)
                await page.locator("button:has-text('Change')").click()
            except Exception as ex:
                pass

            await page.wait_for_selector("label:has-text('Ship')")
            await page.locator("label").filter(has_text="Ship").first.click()
            await page.wait_for_selector('input[name="zipCode"]')
            await page.locator('input[name="zipCode"]').first.fill(str(zipcode))
            await page.locator('button[aria-label="Save ZIP Code"]').first.click()
            main_page_content = await page.content()

            if check_product_stock(main_page_content):
                return first_content, "", 200

            await page.locator(f'form[data-testid="add-to-cart-form-{pid}"] button').click()

            try:#case 1 popup url:https://www.grainger.com/product/15F493
                await page.wait_for_selector('button[name="accept"]',timeout=5000)
                await page.locator('button[name="accept"]').click()
            except Exception as ex:
                pass

            try:#case2 popup url:https://www.grainger.com/product/152K54
                await page.wait_for_selector('[data-testid="dialog-inner-container"]', timeout=5000)
                await page.locator('button:has-text("Agree")').nth(1).click()
            except:
                pass

            try:#Out of stock after clicking add to cart. url:https://www.grainger.com/product/10C897
                after_cart_content=await page.content()
                if check_product_stock(after_cart_content):
                    return first_content, "", 200
            except:
                pass

            await page.wait_for_selector('button:has-text("Continue Shopping")')
            await page.locator('button:has-text("Continue Shopping") >> .. >> a:has-text("View Cart")').click()

            await page.get_by_text("Order Summary").nth(1).hover()
            shipping_content = await page.content()

            return main_page_content, shipping_content, 200

        except Exception as ex:
            traceback.print_exc()
            await page.screenshot(path=f"htmls/{randint(0, 10000)}.jpeg", type="jpeg", full_page=True)

        finally:
            await browser.close()

if __name__=="__main__":
    import asyncio
    asyncio.run(run_scrape("https://www.grainger.com/product/RITTAL-Enclosure-Air-Conditioner-6YDP4", "70001"))