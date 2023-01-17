import uuid
from flask import Flask, request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db import db
from models import TagModel, StoreModel, ItemModel
from schemas import TagSchema, TagAndItemSchema



blp = Blueprint('Tag', __name__, description="Operation on Tag")

@blp.route("/store/<string:store_id>/tag")
class TagInStore(MethodView):
    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        
        return store.tags
    
    @blp.arguments(TagSchema)
    @blp.response(200, TagSchema)
    def post(self, tag_data, store_id):
        if TagModel.query.filter(TagModel.store_id == store_id).first():
            abort(400, message="A tag with that name already exists in that store.")
            
        tag = TagModel(store_id=store_id, **tag_data)
        
        try:
            db.session.add(tag)
            db.session.commit()
            
        except SQLAlchemyError :
            abort(404, message="Cannot be added")  
            
        return tag
    
@blp.route("/item/<string:item_id>/tag/<string:tag_id>")
class LinkTagsToItem(MethodView):
    @blp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        
        item.tags.append(tag)
        
        try:
            db.session.add(item)
            db.session.commit
        except SQLAlchemyError:
            abort(500, message="Cannot be added")
            
        return tag    
    
    @blp.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        
        item.tags.remove(tag)
        
        try:
            db.session.add(item)
            db.session.commit
        except SQLAlchemyError:
            abort(500, message="Cannot be deleted")
            
        return {"message": "Item removed from tag", "item": item, "tag": tag}
    
@blp.route("/tag/<string:tag_id>")
class Tag(MethodView):
    @blp.response(200, TagAndItemSchema)
    def get(self, tag_id):
        return TagModel.query.get_or_404(tag_id)
    
    @blp.response(
        202,
        description="Deletes a tag if no item is tagged with it.",
        example={"message": "Tag deleted."},
    )
    @blp.alt_response(404, description="Tag not found.")
    @blp.alt_response(
        400,
        description="Returned if the tag is assigned to one or more items. In this case, the tag is not deleted.",
    )
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)

        if not tag.items:
            db.session.delete(tag)
            db.session.commit()
            return {"message": "Tag deleted."}
        abort(
            400,
            message="Could not delete tag. Make sure tag is not associated with any items, then try again.",
        )