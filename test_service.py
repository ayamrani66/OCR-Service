import asyncio

from dotenv import load_dotenv

load_dotenv()

from src.services.ocr_service import parse_images


async def main():
    chemin_image = "image2.png"  

    with open(chemin_image, "rb") as f:
        contenu = f.read()

    resultat = await parse_images([(contenu, "image/png", chemin_image)])

    print(resultat.model_dump())


asyncio.run(main())