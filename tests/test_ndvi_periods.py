from crop_labeller.ndvi_periods import period_full_label, period_short_label


def test_period_short_label_covers_full_season():
    assert period_short_label(1) == "Oct (2nd half)"
    assert period_short_label(2) == "Nov (1st half)"
    assert period_short_label(13) == "Apr (2nd half)"
    assert period_short_label(14) == "May (1st half)"


def test_period_full_label_without_year():
    assert period_full_label(1) == "October 2nd half"
    assert period_full_label(6) == "January 1st half"


def test_period_full_label_with_year_rolls_over_for_next_calendar_year():
    # Season starting in 2021: Oct-Dec stay in 2021, Jan-May roll into 2022.
    assert period_full_label(1, season_start_year=2021) == "October 2nd half, 2021"
    assert period_full_label(5, season_start_year=2021) == "December 2nd half, 2021"
    assert period_full_label(6, season_start_year=2021) == "January 1st half, 2022"
    assert period_full_label(14, season_start_year=2021) == "May 1st half, 2022"


def test_period_labels_fall_back_for_out_of_range_steps():
    assert period_short_label(15) == "Step 15"
    assert period_full_label(15) == "Time step 15"


def test_period_full_label_ignores_unparseable_year():
    assert period_full_label(1, season_start_year="unknown") == "October 2nd half"
