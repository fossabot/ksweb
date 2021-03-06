# -*- coding: utf-8 -*-
"""Output model module."""
from string import Template

import tg
from bson import ObjectId
from markupsafe import Markup
from ming import schema as s
from ming.odm import FieldProperty, ForeignIdProperty, RelationProperty
from ming.odm.declarative import MappedClass
from datetime import datetime
from ksweb.model import DBSession, User


def _custom_title(obj):
    return Markup("<a href='%s'>%s</a>" % (tg.url('/output/edit', params=dict(_id=obj._id, workspace=obj._category)), obj.title))


def _content_preview(obj):
    return " ".join(Markup(obj.html).striptags().split()[:5])


class Output(MappedClass):

    class __mongometa__:
        session = DBSession
        name = 'output'
        indexes = [
            ('title',),
        ]

    __ROW_COLUM_CONVERTERS__ = {
        'title': _custom_title,
        'content': _content_preview
    }

    _id = FieldProperty(s.ObjectId)

    title = FieldProperty(s.String, required=True)
    content = FieldProperty(s.Anything, required=True)
    """
    Possible content of the output is a list with two elements type:
        - text
        - precondition_response

    If the type is text the content contain the text
    If the type is qa_response the content contain the obj id of the related precondition/response


    An example of the content is this
    "content" : [
        {
            "content" : "Simple text",
            "type" : "text",
            "title" : ""
        },
        {
            "content" : "57723171c42d7513bb31e17d",
            "type" : "qa_response",
            "title" : "Colori"
        }
    ]

    """

    html = FieldProperty(s.String, required=True, if_missing='')

    _owner = ForeignIdProperty('User')
    owner = RelationProperty('User')

    _precondition = ForeignIdProperty('Precondition')
    precondition = RelationProperty('Precondition')

    _category = ForeignIdProperty('Category')
    category = RelationProperty('Category')

    public = FieldProperty(s.Bool, if_missing=True)
    visible = FieldProperty(s.Bool, if_missing=True)

    created_at = FieldProperty(s.DateTime, if_missing=datetime.utcnow())

    @classmethod
    def output_available_for_user(cls, user_id, workspace=None):
        return User.query.get(_id=user_id).owned_entities(cls, workspace)

    @property
    def human_readbale_content(self):
        #  TODO: Non appena saranno aggiornati gli output, bisogna modificare questa property affinche restituisca dei valori leggibili

        #res = []
        #for elem in self.content:
            #if elem is testo ok
            # else mostra una stringa di dettaglio del filtro
        return self.content

    @property
    def entity(self):
        return 'output'

    @property
    def upcast(self):
        from ksweb.lib.utils import _upcast

        """
        This property replace widget placeholder into html widget

        {output_589066e6179280afa788035e}
            ->
        <span class="objplaceholder output-widget output_589066e6179280afa788035e"></span>
        """
        return _upcast(self)

    def render(self, evaluations_dict):
        html = Template(self.html)
        nested_output_html = dict()

        if str(self._id) not in evaluations_dict:
            return ''
        if evaluations_dict[str(self._id)]['evaluation'] is False:
            return ''

        for elem in self.content:
            if elem['type'] == 'output':
                nested_output = Output.query.get(_id=ObjectId(elem['content']))
                nested_output_html['output_' + elem['content']] = nested_output.render(evaluations_dict)

        return html.safe_substitute(**nested_output_html)

    def __json__(self):
        from ksweb.lib.utils import to_dict
        _dict = to_dict(self)
        _dict['entity'] = self.entity
        return _dict


__all__ = ['Output']
