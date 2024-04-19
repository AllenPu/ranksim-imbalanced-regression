#python train.py  --batch_size 256 --lr 1e-3 --reweight sqrt_inv --lds --lds_kernel gaussian --lds_ks 5 --lds_sigma 2 --norm
#echo 'LDS feature norm'
python train.py --batch_size 256 --lr 1e-3 --fds --fds_kernel gaussian --fds_ks 5 --fds_sigma 2 --norm
echo 'FDS feature norm'
#python train.py  --batch_size 256 --lr 2.5e-4 --reweight sqrt_inv --regularization_weight=100.0 --interpolation_lambda=2.0 --weight_norm
#echo 'RankSim and square-root frequency inverse weight norm'
#python train.py --batch_size 256 --lr 2.5e-4 --reweight sqrt_inv --lds --lds_kernel gaussian --lds_ks 5 --lds_sigma 2 --regularization_weight=100.0 --interpolation_lambda=2.0 --weight_norm
#echo 'RankSim and LDS weight norm'
#python train.py --batch_size 256 --lr 2.5e-4 --reweight sqrt_inv --lds --lds_kernel gaussian --lds_ks 5 --lds_sigma 2 --fds --fds_kernel gaussian --fds_ks 5 --fds_sigma 2 --regularization_weight=100.0 --interpolation_lambda=2.0 --weight_norm
#echo 'RankSim and LDS + FDS weight norm'
#python train.py  --batch_size 256 --lr 1e-3 --reweight sqrt_inv --lds --lds_kernel gaussian --lds_ks 5 --lds_sigma 2 --norm
#echo 'LDS feature norm'
#python train.py --batch_size 256 --lr 1e-3 --fds --fds_kernel gaussian --fds_ks 5 --fds_sigma 2 --norm
#echo 'FDS feature norm'
#python train.py  --batch_size 64 --lr 2.5e-4 --reweight sqrt_inv --regularization_weight=100.0 --interpolation_lambda=2.0 --norm
#echo 'RankSim and square-root frequency inverse  feature norm'
#python train.py --batch_size 64 --lr 2.5e-4 --reweight sqrt_inv --lds --lds_kernel gaussian --lds_ks 5 --lds_sigma 2 --regularization_weight=100.0 --interpolation_lambda=2.0 --norm
#echo 'RankSim and LDS feature norm'
#python train.py --batch_size 64 --lr 2.5e-4 --reweight sqrt_inv --lds --lds_kernel gaussian --lds_ks 5 --lds_sigma 2 --fds --fds_kernel gaussian --fds_ks 5 --fds_sigma 2 --regularization_weight=100.0 --interpolation_lambda=2.0 --norm
#echo 'RankSim and LDS + FDS feature norm'
#python train.py  --batch_size 256 --lr 1e-3 --reweight sqrt_inv --lds --lds_kernel gaussian --lds_ks 5 --lds_sigma 2 --weight_norm --norm
#echo 'LDS weight feature norm'
#python train.py --batch_size 256 --lr 1e-3 --fds --fds_kernel gaussian --fds_ks 5 --fds_sigma 2 --weight_norm --norm
#echo 'FDS weight feature norm'
#python train.py  --batch_size 64 --lr 2.5e-4 --reweight sqrt_inv --regularization_weight=100.0 --interpolation_lambda=2.0 --weight_norm --norm
#echo 'RankSim and square-root frequency inverse weight feature norm'
#python train.py --batch_size 64 --lr 2.5e-4 --reweight sqrt_inv --lds --lds_kernel gaussian --lds_ks 5 --lds_sigma 2 --regularization_weight=100.0 --interpolation_lambda=2.0 --weight_norm --norm
#echo 'RankSim and LDS weight feature norm'
#python train.py --batch_size 64 --lr 2.5e-4 --reweight sqrt_inv --lds --lds_kernel gaussian --lds_ks 5 --lds_sigma 2 --fds --fds_kernel gaussian --fds_ks 5 --fds_sigma 2 --regularization_weight=100.0 --interpolation_lambda=2.0 --weight_norm --norm
#echo 'RankSim and LDS + FDS weight feature norm'