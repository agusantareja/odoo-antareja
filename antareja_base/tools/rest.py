import logging
import werkzeug.wrappers
import ast

try:
    import simplejson as json
except ImportError:
    import json

from datetime import datetime, date
from odoo.fields import Datetime, Date, Many2many, One2many
from odoo.http import request

_logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("utf-8")
        if isinstance(obj, datetime):
            return Datetime.to_string(obj)
        if isinstance(obj, date):
            return Date.to_string(obj)
        return json.JSONEncoder.default(self, obj)

def get_body_json():
    data = {}
    data_str = request.httprequest.data.decode("utf-8")
    if data_str:
        try:
            data = json.loads(data_str)
            if isinstance(data, str):
                data=json.loads(data)
        except:
            pass

# Handle responses


def valid_response(status, data):
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps(data, cls=JSONEncoder),
    )


def invalid_response(status, error, info=""):
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps({
            'error': error,
            'error_descrip': info,
        }),
    )


def invalid_object_id():
    _logger.error("Invalid object 'id'!")
    return invalid_response(
        400, 'invalid_object_id', "Invalid object 'id'!"
    )


def invalid_token():
    _logger.error("Token is expired or invalid!")
    return invalid_response(
        401, 'invalid_token', "Token is expired or invalid!"
    )


def modal_not_found(modal_name):
    _logger.error("Not found object(s) in odoo!")
    return invalid_response(
        404, 'object_not_found_in_odoo', "Modal " + modal_name + " Not Found!"
    )


def rest_api_unavailable(modal_name):
    _logger.error("Not found object(s) in odoo!")
    return invalid_response(
        404, 'object_not_found_in_odoo', "Enable Rest API For " + modal_name + "!"
    )


def object_not_found_all(modal_name):
    _logger.error("Not found object(s) in odoo!")
    return invalid_response(
        404, 'object_not_found_in_odoo', "No Record found in " + modal_name + "!"
    )


def object_not_found(record_id, modal_name):
    _logger.error("Not found object(s) in odoo!")
    return invalid_response(
        404, 'object_not_found_in_odoo', "Record " + str(record_id) + " Not found in " + modal_name + "!"
    )


def unable_delete():
    _logger.error("Access Denied!")
    return invalid_response(
        403, "you don't have access to delete records for " "this model", "Access Denied!"
    )


def no_object_created(odoo_error):
    _logger.error("Not created object in odoo! ERROR: %s" % odoo_error)
    return invalid_response(
        500, 'not_created_object_in_odoo', "Not created object in odoo! ERROR: %s" % odoo_error
    )


def no_object_updated(odoo_error):
    _logger.error("Not updated object in odoo! ERROR: %s" % odoo_error)
    return invalid_response(
        500, 'not_updated_object_in_odoo', "Object Not Updated! ERROR: %s" % odoo_error
    )


def no_object_deleted(odoo_error):
    _logger.error("Not deleted object in odoo! ERROR: %s" % odoo_error)
    return invalid_response(
        500, 'not_deleted_object_in_odoo', "Not deleted object in odoo! ERROR: %s" % odoo_error
    )


# request


def eval_json_to_data(modelname, json_data, create=True):
    Model = request.env[modelname]
    model_fiels = Model._fields
    field_name = [name for name, field in Model._fields.items()]
    values = {}
    for field in json_data:
        if field not in field_name:
            continue
        if field not in field_name:
            continue
        val = json_data[field]
        if not isinstance(val, list):
            values[field] = val
        else:
            values[field] = []
            if not create and isinstance(model_fiels[field], Many2many):
                values[field].append((5,))
            for res in val:
                recored = {}
                for f in res:
                    recored[f] = res[f]
                if isinstance(model_fiels[field], Many2many):
                    values[field].append((4, recored['id']))

                elif isinstance(model_fiels[field], One2many):
                    if create:
                        values[field].append((0, 0, recored))
                    else:
                        if 'id' in recored:
                            id = recored['id']
                            del recored['id']
                            values[field].append((1, id, recored)) if len(recored) else values[field].append((2, id))
                        else:
                            values[field].append((0, 0, recored))
    return values


def object_read(model_name, params, status_code, filter_fields=None, __from_sync_data_api=True):
    domain = []
    fields = []
    offset = 0
    limit = None
    order = None
    if 'filters' in params:
        domain += ast.literal_eval(params['filters'])
    if 'field' in params:
        fields += ast.literal_eval(params['field'])
    if 'offset' in params:
        offset = int(params['offset'])
    if 'limit' in params:
        limit = int(params['limit'])
    if 'order' in params:
        order = params['order']

    data = request.env[model_name].with_context(__from_sync_data_api=__from_sync_data_api).search_read(
        domain=domain, fields=fields, offset=offset, limit=limit, order=order
    )
    if data:
        return valid_response(status=status_code, data={
            'count': len(data),
            'results': data
        })
    else:
        return object_not_found_all(model_name)


def object_read_one(model_name, rec_id, params, status_code, filter_fields=None, __from_sync_data_api=True):
    fields = []
    if 'field' in params:
        fields += ast.literal_eval(params['field'])
        if filter_fields:
            fields = filter_fields(model_name, fields)
    try:
        rec_id = int(rec_id)
    except Exception as e:
        rec_id = False

    if not rec_id:
        return invalid_object_id()
    data = request.env[model_name].search_read(domain=[('id', '=', rec_id)], fields=fields)
    if data:
        return valid_response(status=status_code, data=data)
    else:
        return object_not_found(rec_id, model_name)


def object_create_one(model_name, data, status_code):
    try:
        res = request.env[model_name].create(data)
    except Exception as e:
        return no_object_created(e)
    if res:
        return valid_response(status_code, {'id': res.id})


def object_update_one(model_name, rec_id, data, status_code):
    try:
        rec_id = int(rec_id)
    except Exception as e:
        rec_id = None

    if not rec_id:
        return invalid_object_id()

    try:
        res = request.env[model_name].search([('id', '=', rec_id)])
        if res:
            res.write(data)
        else:
            return object_not_found(rec_id, model_name)
    except Exception as e:
        return no_object_updated(e)
    if res:
        return valid_response(status_code, {'desc': 'Record Updated successfully!', 'update': True})


def object_delete_one(model_name, rec_id, status_code):
    try:
        rec_id = int(rec_id)
    except Exception as e:
        rec_id = None

    if not rec_id:
        return invalid_object_id()

    try:
        res = request.env[model_name].search([('id', '=', rec_id)])
        if res:
            res.unlink()
        else:
            return object_not_found(rec_id, model_name)
    except Exception as e:
        return no_object_deleted(e)
    if res:
        return valid_response(status_code, {'desc': 'Record Successfully Deleted!', 'delete': True})
