#echo 'LDS '
#python train.py  --batch_size 256 --lr 1e-3 --reweight sqrt_inv --lds --lds_kernel gaussian --lds_ks 5 --lds_sigma 2 --weight_norm
#echo 'FDS'
#python train.py --batch_size 256 --lr 1e-3 --fds --fds_kernel gaussian --fds_ks 5 --fds_sigma 2 --weight_norm
#echo 'FDS'
#python train.py  --batch_size 64 --lr 2.5e-4 --reweight sqrt_inv --regularization_weight=100.0 --interpolation_lambda=2.0 --weight_norm
#echo 'RankSim and square-root frequency inverse'
#echo 'RankSim and LDS'
python train.py --batch_size 64 --lr 2.5e-4 --reweight sqrt_inv --lds --lds_kernel gaussian --lds_ks 5 --lds_sigma 2 --regularization_weight=100.0 --interpolation_lambda=2.0 --weight_norm
echo 'RankSim and LDS'
#python train.py --batch_size 64 --lr 2.5e-4 --reweight sqrt_inv --lds --lds_kernel gaussian --lds_ks 5 --lds_sigma 2 --fds --fds_kernel gaussian --fds_ks 5 --fds_sigma 2 --regularization_weight=100.0 --interpolation_lambda=2.0 --weight_norm
#echo 'RankSim and LDS + FDS'