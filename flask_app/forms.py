from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField
from wtforms.validators import InputRequired, Length, NumberRange

class FlightRequestForm(FlaskForm):
    fly_from = StringField('Fly From', validators=[InputRequired(), Length(max=3)])
    fly_to = StringField('Fly To', validators=[InputRequired(), Length(max=3)])
    date_from = StringField('Date From', validators=[InputRequired()])
    date_to = StringField('Date To', validators=[InputRequired()])
    return_from = StringField('Return From', validators=[InputRequired()])
    return_to = StringField('Return To', validators=[InputRequired()])
    nights_in_dst_from = IntegerField('Nights in Destination (From)', validators=[NumberRange(min=0)])
    nights_in_dst_to = IntegerField('Nights in Destination (To)', validators=[NumberRange(min=0)])
    flight_type = SelectField('Flight Type', choices=[('one-way', 'One-way'), ('round', 'Round')], validators=[InputRequired()])
    adults = StringField('Number of Adults', validators=[InputRequired()])
    curr = StringField('Currency', validators=[InputRequired(), Length(max=3)])
    sort = StringField('Sort', validators=[InputRequired()])
    selected_cabins = StringField('Selected Cabins', validators=[InputRequired(), Length(max=1)])
    limit = IntegerField('Limit', validators=[NumberRange(min=0)])
