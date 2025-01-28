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
            block_images=True,
            block_webgl=True,
            block_webrtc=True,
            os=["windows"],
            headless="virtual",
            i_know_what_im_doing=True,
            geoip=True,
            webgl_config=("Google Inc. (NVIDIA)", "ANGLE (NVIDIA, NVIDIA GeForce GTX 980 Direct3D11 vs_5_0 ps_5_0), or similar"),
            fonts=["Arial", "Arial Black", "Bahnschrift", "Calibri", "Calibri Light", "Cambria", "Cambria Math", "Candara", "Candara Light", "Comic Sans MS", "Consolas", "Constantia", "Corbel", "Corbel Light", "Courier New", "Ebrima", "Franklin Gothic Medium", "Gabriola", "Gadugi", "Georgia", "HoloLens MDL2 Assets", "Impact", "Ink Free", "Javanese Text", "Leelawadee UI", "Leelawadee UI Semilight", "Lucida Console", "Lucida Sans Unicode", "MS Gothic", "MS PGothic", "MS UI Gothic", "MV Boli", "Malgun Gothic", "Malgun Gothic Semilight", "Marlett", "Microsoft Himalaya", "Microsoft JhengHei", "Microsoft JhengHei Light", "Microsoft JhengHei UI", "Microsoft JhengHei UI Light", "Microsoft New Tai Lue", "Microsoft PhagsPa", "Microsoft Sans Serif", "Microsoft Tai Le", "Microsoft YaHei", "Microsoft YaHei Light", "Microsoft YaHei UI", "Microsoft YaHei UI Light", "Microsoft Yi Baiti", "MingLiU-ExtB", "MingLiU_HKSCS-ExtB", "Mongolian Baiti", "Myanmar Text", "NSimSun", "Nirmala UI", "Nirmala UI Semilight", "PMingLiU-ExtB", "Palatino Linotype", "Segoe Fluent Icons", "Segoe MDL2 Assets", "Segoe Print", "Segoe Script", "Segoe UI", "Segoe UI Black", "Segoe UI Emoji", "Segoe UI Historic", "Segoe UI Light", "Segoe UI Semibold", "Segoe UI Semilight", "Segoe UI Symbol", "Segoe UI Variable", "SimSun", "SimSun-ExtB", "Sitka", "Sitka Text", "Sylfaen", "Symbol", "Tahoma", "Times New Roman", "Trebuchet MS", "Twemoji Mozilla", "Verdana", "Webdings", "Wingdings", "Yu Gothic", "Yu Gothic Light", "Yu Gothic Medium", "Yu Gothic UI", "Yu Gothic UI Light", "Yu Gothic UI Semibold", "Yu Gothic UI Semilight", "宋体", "微軟正黑體", "微軟正黑體 Light", "微软雅黑", "微软雅黑 Light", "新宋体", "新細明體-ExtB", "游ゴシック", "游ゴシック Light", "游ゴシック Medium", "細明體-ExtB", "細明體_HKSCS-ExtB", "맑은 고딕", "맑은 고딕 Semilight", "ＭＳ ゴシック", "ＭＳ Ｐゴシック"],
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