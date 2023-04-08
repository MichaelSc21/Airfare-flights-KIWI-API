from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import InputRequired, Length, NumberRange, Optional


class RequiredUnless(InputRequired, NumberRange):
    def __init__(self, other_field_name, values, message=None, min=None):
        self.other_field_name = other_field_name
        self.values = values
        self.message = message


    def __call__(self, form, field):
        other_field_value = form[self.other_field_name].data
        if other_field_value is None:
            raise Exception('no field named "%s" in form' % self.other_field)
        # If flight_type is round(so if it is not in values), then this field is required
        print('It got all the way here')
        if other_field_value not in self.values: 
            if min!=None:
                super(NumberRange, self).__call__(form, field, min=0)
            else:
                super(InputRequired, self).__call__(form, field)
        # If this flight_type is one-way, then this field is optional
        else:
            Optional().__call__(form, field)




class FlightRequestForm(FlaskForm):
    fly_from = StringField('Fly From', validators=[InputRequired(), Length(max=3)])
    fly_to = StringField('Fly To', validators=[InputRequired(), Length(max=3)])
    date_from = StringField('Date From', validators=[InputRequired()])
    date_to = StringField('Date To', validators=[InputRequired()])

    return_from = StringField('Return From', validators=[RequiredUnless('flight_type', 'One-way')])  # noqa: E501
    return_to = StringField('Return To', validators=[RequiredUnless('flight_type', 'One-way')])  # noqa: E501
    nights_in_dst_from = IntegerField('Nights in Destination (From)', validators=[RequiredUnless('flight_type', 'One-way', min=0)])  # noqa: E501
    nights_in_dst_to = IntegerField('Nights in Destination (To)', validators=[RequiredUnless('flight_type', 'One-way', min=0)])  # noqa: E501

    flight_type = SelectField('Flight Type', choices=[('One-way'), ('Round')], validators=[InputRequired()])
    adults = StringField('Number of Adults', validators=[InputRequired()])
    curr = StringField('Currency', validators=[InputRequired(), Length(max=3)])
    #sort = StringField('Sort', validators=[InputRequired()])
    selected_cabins = SelectField('Selected Cabins', 
                                  choices=[('M', 'M (Economy Class)'), 
                                           ('W', 'W (Economy Premium)'), 
                                           ('C', 'C (Business Class)'), 
                                           ('F', 'F (First Class)')], validators=[InputRequired()])
    #limit = IntegerField('Limit', validators=[NumberRange(min=0)])
    submit = SubmitField('Submit')
