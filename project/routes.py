# Textext/project/routes.py

import os
import json
import random
import time
import threading
from datetime import datetime
import pandas as pd

from flask import (
    Blueprint,
    render_template,
    current_app,
    request,
    jsonify,
    session,
    redirect,
    url_for,
)
from flask_socketio import SocketIO, emit

from project.utils.backend_operations import ImageHandler
from project.utils.database_operations import DatabaseHandler

main = Blueprint("main", __name__)


@main.route("/")
@main.route("/home")
def index():
    return render_template("index.html")


@main.route("/upload_images", methods=["GET", "POST"])
def upload_images():
    if request.method == "GET":
        # If GET, render the uploaded files
        uploaded_files = os.listdir("image_uploads")

        df = pd.DataFrame(uploaded_files, columns=["Files"])
        df["Links"] = df.apply(
            lambda row: f'<a href={row["Files"]} class="text-blue-500 hover:text-blue-700"">View</a>',
            axis=1,
        )

        # Add an index column
        df.index += 1  # Make ID start from 1 instead of 0
        df.index.name = "ID"
        df.reset_index(inplace=True)

        # Convert dataframe to HTML
        table_html = df.to_html(
            classes="table table-striped",
            index=False,
            table_id="sortable-table",
            escape=False,
        )
        return render_template("upload.html", table=table_html)
    else:
        result = ImageHandler.add_images(request)
        return result


@main.route("/select_models/<int:batch_id>", methods=["GET", "POST"])
def select_models(batch_id):
    if request.method == "GET":
        # get the model names and availabilty status from the database
        query = """
            SELECT 
                name, available
            FROM models
        """

        result = DatabaseHandler.execute_query(query=query, query_type="fetchall")

        if result:
            models_list = result
        else:
            models_list = []

        return render_template(
            "select_models.html", models_list=models_list, batch_id=batch_id
        )
    else:
        models_list = request.form.getlist("model")

        # save this list of models into corresponding batches record
        ImageHandler.store_models_for_batch(models_list=models_list, batch_id=batch_id)

        # and then redirect to extract_text page
        return redirect(url_for("extract_text", batch_id=batch_id))


@main.route("/extract_text/<int:batch_id>")
def extract_text(batch_id):
    # Your text extraction logic here
    # fetch how many images for this batch has been processed:
    # if done then redirect to results page
    # if some images remaining start processing them one by one
    # and send the results to user
    # and update the database as well.

    query = """
        SELECT 
            cardinality(models_list), cardinality(processed_models_list)
        FROM batches 
        WHERE batch_id = %s
    """
    args = (batch_id,)

    result = DatabaseHandler.execute_query(
        query=query, query_type="fetchone", args=args
    )

    if result:
        num_models, num_models_processed = result
        print(
            f"Result: {result}, Num Models: {num_models}\
            , Num Models Processed: {num_models_processed}"
        )

        if num_models > num_models_processed:
            return render_template("text_extraction_progress.html", batch_id=batch_id)
        else:
            # we will just redirect to the results page.
            return redirect(url_for("index"))
    else:
        # no such record exists!!
        return redirect(url_for("index"))


"""
@socketio.on('connect', namespace='/image_processed')
def connect():
    print('Client connected')
    # Get the batch_id parameter from the connection URL
    batch_id = request.args.get('batch_id', type=int)  
    img_processing_thread = threading.Thread(
        target=process_images, 
        args = (batch_id,)
    )
    img_processing_thread.daemon = True
    img_processing_thread.start()

@socketio.on('disconnect', namespace='/image_processed')
def disconnect():
    print('Client disconnected')
"""
