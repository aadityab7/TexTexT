# TexTexT/app/utils/backend_operations.py

import os
from flask import request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename

from project.utils.database_operations import DatabaseHandler
from project.extensions import socketio


class ImageHandler:
    @staticmethod
    def create_batch(num_images: int = 0):
        """
        Function to create a new batch and return its batch number
        """
        query = """
            INSERT INTO batches 
                (num_images) 
            VALUES (%s)
            RETURNING batch_id
        """
        args = (num_images,)

        result = DatabaseHandler.execute_query(
            query=query, query_type="fetchone", args=args
        )
        batch_id = result[0]

        return batch_id

    @staticmethod
    def insert_image(batch_id: int, url: str):
        """
        Function to insert image details into the database
        """
        query = """
            INSERT INTO images (batch_id, url) 
            VALUES (%s, %s)
        """

        args = (batch_id, url)

        DatabaseHandler.execute_query(query=query, query_type="commit", args=args)

    @staticmethod
    def num_images_processed_by_model(model_id: int, batch_id: int):
        query = """
            SELECT 
                num_processed
            FROM batch_model_progress 
            WHERE 
                batch_id = %s
                AND
                model_id = %s
        """

        args = (batch_id, model_id)

        result = DatabaseHandler.execute_query(
            query=query, query_type="fetchone", args=args
        )

        if result:
            num_images_processed = result[0]
        else:
            # If no record exists, insert a new record with default values
            query = """
                INSERT INTO 
                batch_model_progress 
                    (batch_id, model_id)
                VALUES 
                    (%s, %s)
            """

            args = (batch_id, model_id)

            DatabaseHandler.execute_query(query=query, query_type="commit", args=args)

            # Since no record was found, set num_images_processed to the default value
            num_images_processed = 0

        return num_images_processed

    @staticmethod
    def process_images(batch_id: int):
        query = """
            SELECT 
                models_list, processed_models_list
            FROM batches 
            WHERE batch_id = %s
        """

        args = (batch_id,)

        result = DatabaseHandler.execute_query(
            query=query, query_type="fetchone", args=args
        )

        if result:
            models_list, processed_models_list = result
        else:
            models_list, processed_models_list = [], []

        num_models = len(models_list)
        num_models_processed = len(processed_models_list)

        query = """
            SELECT 
                image_id, url
            FROM images 
            WHERE batch_id = %s
            ORDER BY image_id
        """

        args = (batch_id,)

        list_of_images = DatabaseHandler.execute_query(
            query=query, query_type="fetchall", args=args
        )

        num_images = len(list_of_images)

        for model_idx, model_id in enumerate(models_list):
            if model_id not in processed_models_list:

                query = """
                    SELECT 
                        name, available
                    FROM models
                    WHERE model_id = %s
                """

                args = (model_id,)

                result = DatabaseHandler.execute_query(
                    query=query, query_type="fetchone", args=args
                )

                if result:
                    model_name, model_available = result
                else:
                    model_name, model_available = "", False

                if not model_available:
                    # move on from this model and process with others
                    continue

                # use each model to process all the images in a batch
                # check how many images have already been processed
                # by this model for this batch
                num_images_processed = ImageHandler.num_images_processed_by_model(
                    model_id=model_id, batch_id=batch_id
                )

                for image_idx, (image_id, image_url) in enumerate(
                    list_of_images[num_images_processed:]
                ):
                    # pass the image_id, image_url and model_id to process_image

                    print(image_id, image_url, model_id, model_name)

                    extraction_status, extracted_text = ImageHandler.process_image(
                        image_id=image_id,
                        image_url=image_url,
                        model_id=model_id,
                        model_name=model_name,
                    )

                    if extraction_status == "OK":

                        # update the num_processed of batch for this model
                        # as another image is processed
                        query = """
                            UPDATE 
                            batch_model_progress
                            SET num_processed = num_processed + 1
                            WHERE
                                batch_id = %s
                                AND 
                                model_id = %s
                        """

                        args = (batch_id, model_id)

                        DatabaseHandler.execute_query(
                            query=query, query_type="commit", args=args
                        )

                        progress_update_text = f"Processing with model: {model_name}"
                        progress_update_text += f"\nImages Processed: {image_idx + num_images_processed + 1} / {num_images}"
                        progress_update_text += (
                            f"\nCurrent Text Extracted: {extracted_text}"
                        )

                        socketio.emit(
                            "image_processed",
                            {"progress_update_text": progress_update_text},
                            namespace="/image_processed",
                        )
                # end of image for loop

                socketio.emit("model_process_complete", namespace="/image_processed")

                # current model_id completed processing
                # add this to the processed_models_list in db
                query = """
                    UPDATE batches
                    SET processed_models_list = array_append(
                                                    processed_models_list, 
                                                    %s
                                                )
                    WHERE batch_id = %s
                """

                args = (model_id, batch_id)

                DatabaseHandler.execute_query(
                    query=query, query_type="commit", args=args
                )
        # end of models for loop

        # Emit countdown_finished event
        socketio.emit("image_processing_finished", namespace="/image_processed")

    @staticmethod
    def process_image(image_id: int, image_url: str, model_id: int, model_name: str):
        status = "WAIT"

        # extracted_text = ocr.extract_text(
        #     file_path = image_url,
        #     model_to_use = model_name
        # )

        extracted_text = ""

        print(f"extracted_text: {extracted_text}")

        # text has been extracted now update the database
        # store the extracted text for image by the model
        query = """
            INSERT INTO
            extracted_texts
                (model_id, image_id, extracted_text)
            VALUES
                (%s, %s, %s)
        """

        args = (model_id, image_id, extracted_text)

        DatabaseHandler.execute_query(query=query, query_type="commit", args=args)

        status = "OK"
        return status, extracted_text

    @staticmethod
    def store_models_for_batch(models_list: list, batch_id: int):
        query = """
            SELECT 
                name, model_id
            FROM models
        """

        list_of_models = DatabaseHandler.execute_query(
            query=query, query_type="fetchall"
        )

        if not list_of_models:
            list_of_models = []

        model_id_name_mapping = dict(list_of_models)
        model_id_list = []

        for model_name in models_list:
            print(model_name)
            model_id = model_id_name_mapping.get(model_name, -1)
            print(model_id)
            if model_id != -1:
                model_id_list.append(model_id)

        query = """
            UPDATE batches
            SET models_list = %s
            WHERE batch_id = %s
        """
        args = (model_id_list, batch_id)

        DatabaseHandler.execute_query(query=query, query_type="commit", args=args)

    @staticmethod
    def add_images(request):
        print(request.files)
        if "files" not in request.files:
            return jsonify({"error": "No images uploaded!!"})

        images = request.files.getlist("files")

        if not images:
            return jsonify({"error": "No Images Uploaded!!"})

        # batch_id = create_batch(len(images))
        uploaded_paths = []

        for image in images:
            # Generate a secure filename and save the image locally
            # later this will be updated to store the files in the cloud
            filename = secure_filename(image.filename)
            upload_folder = "image_uploads"
            os.makedirs(upload_folder, exist_ok=True)
            local_path = os.path.join(upload_folder, filename)
            image.save(local_path)
            uploaded_paths.append(local_path)

            # Insert image details into the database
            # insert_image(batch_id, local_path)

        print("Uploaded Paths: ", uploaded_paths)

        return jsonify({"batch_id": uploaded_paths})
