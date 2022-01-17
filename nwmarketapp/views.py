
from django.shortcuts import render
from nwmarketapp.models import ConfirmedNames
from nwmarketapp.models import Prices
from django.http import JsonResponse
import numpy as np
from django.db.models.functions import TruncDay
from django.db.models import Count
import itertools

def remove_outliers(data, m=2.6):
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d / mdev if mdev else 0.
    good_list = data[s < m].tolist()
    bad_indices = np.nonzero(s > m)
    return good_list, bad_indices






def index(request):
    confirmed_names = ConfirmedNames.objects.all().exclude(name__contains='"')
    confirmed_names = confirmed_names.values_list('name', 'id')
    no_outliers = ''
    mean_price = ''
    last_checked = ''

    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if request.method == 'GET' and is_ajax:
        selected_name = request.GET.get('cn_id')
        if selected_name:
            qs_current_price = Prices.objects.filter(name_id=selected_name)
            current_price = list(qs_current_price.values_list('price', flat=True).order_by('timestamp'))
            last_checked = qs_current_price.values_list('timestamp', flat=True).order_by('price')[:1].first()
            hist_price = list(qs_current_price.values_list('timestamp', 'price').order_by('price'))
            hist_price.sort()
            hist_dates, hist_price_list = zip(*hist_price)
            filtered_prices, bad_indices = remove_outliers(np.array(hist_price_list))
            for x in bad_indices[0][::-1]:
                hist_price.pop(x)
            #gets the lowest price for each day
            hist_price_lowest = [(dt, min(v for d, v in grp)) for dt, grp in itertools.groupby(hist_price, key=lambda x: x[0].date())]
            test1 = hist_price_lowest = [(dt, min(v for d, v in grp)) for dt, grp in itertools.groupby(hist_price, key=lambda x: x[0].date())]
            # hist_days = qs_current_price.annotate(day=TruncDay('timestamp')).values_list('day', ).annotate(c=Count('id')).order_by()
            recent_lowest_price = hist_price_lowest[-1::]


            if current_price:
                no_outliers, nothing = remove_outliers(np.array(current_price))
                mean_price = np.mean(no_outliers[0])
                mean_price = '{:.2f}'.format(mean_price)


            else:
                lowest_price = 'Not Found'
            return JsonResponse({"mean_price": mean_price, "recent_lowest_price": recent_lowest_price, "last_checked": last_checked,
                                 "hist_price": hist_price_lowest}, status=200)

        else:
            return JsonResponse({'nothing': True}, status=200)




    return render(request, 'nwmarketapp/index.html', {'cn_list': confirmed_names})

